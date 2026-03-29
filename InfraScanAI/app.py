from flask import Flask, request, jsonify, send_file, render_template, send_from_directory
from flask_cors import CORS
import os
import uuid
import random
from datetime import datetime
from models import db, Report
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io

app = Flask(__name__)
CORS(app)

# Database Setup
basedir = os.path.abspath(os.path.dirname(__name__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# File uploads config
UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
CERT_FOLDER = os.path.join(basedir, 'certificates')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CERT_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db.init_app(app)

with app.app_context():
    db.create_all()

# --- Mock AI Detection Function ---
def mock_ai_detection(image_path):
    # Try to determine file size as a deterministic seed for our mock
    # This ensures the same image file generally gets the same result
    try:
        file_size = os.path.getsize(image_path)
    except OSError:
        file_size = 1024
        
    # Step 1: Check if the image likely contains a road surface
    # We use a simple modulus of file size to reliably determine "road" vs "not road" for the mock.
    # Let's say 10% of images are flagged as non-road.
    is_road = (file_size % 10) != 0
    
    if not is_road:
        return {
            'status': 'success',
            'damage_type': 'No Damage',
            'severity': 'None',
            'confidence': 0.95,
            'message': 'No road damage detected in this image.'
        }
    
    # Step 2: If road is detected, classify damage
    # We use file size to deterministically pick pothole vs crack vs no damage
    damage_val = file_size % 3
    if damage_val == 0:
        damage = 'Pothole'
        severity = 'High'
    elif damage_val == 1:
        damage = 'Crack'
        severity = 'Medium'
    else:
        damage = 'No Damage'
        severity = 'None'

    return {
        'status': 'success',
        'damage_type': damage,
        'severity': severity,
        'confidence': float(f"{0.80 + ((file_size % 20) / 100.0):.2f}"),
        'message': 'Road damage analysis complete.'
    }

# --- Routes ---

@app.route('/static/uploads/<filename>')
def serve_upload(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/citizen_login')
def citizen_login_page():
    return render_template('citizen_login.html')

@app.route('/report')
def report_page():
    return render_template('report.html')

@app.route('/result/<report_id>')
def result_page(report_id):
    return render_template('result.html', report_id=report_id)

@app.route('/my_reports')
def my_reports_page():
    return render_template('my_reports.html')

@app.route('/officer_login')
def officer_login_page():
    return render_template('officer_login.html')

@app.route('/admin')
def admin_page():
    return render_template('admin.html')

@app.route('/success')
def success_page():
    return render_template('success.html')

# --- API Endpoints ---

@app.route('/api/report', methods=['POST'])
def submit_report():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
        
    image = request.files['image']
    if image.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone', '')
    notes = request.form.get('notes', '')
    latitude = form_float(request.form.get('latitude'))
    longitude = form_float(request.form.get('longitude'))
    
    if not name or not email or latitude is None or longitude is None:
        return jsonify({'error': 'Missing required fields'}), 400

    # Save image
    filename = f"{uuid.uuid4().hex}_{image.filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image.save(filepath)

    # Call Mock AI Detection
    detection_result = mock_ai_detection(filepath)

    # Create Report
    report_id = f"REP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{random.randint(100, 999)}"
    
    new_report = Report(
        report_id=report_id,
        name=name,
        email=email,
        phone=phone,
        image_path=filename,
        latitude=latitude,
        longitude=longitude,
        damage_type=detection_result['damage_type'],
        severity=detection_result['severity'],
        confidence=detection_result['confidence'],
        notes=notes
    )
    
    db.session.add(new_report)
    db.session.commit()

    return jsonify({
        'message': 'Report submitted successfully',
        'report_id': report_id,
        'detection': detection_result
    }), 201

def form_float(val):
    try:
        return float(val)
    except (TypeError, ValueError):
        return None

@app.route('/api/detect', methods=['POST'])
def test_detect():
    """Mock standalone endpoint for AI detection, if frontend wants to call it separately"""
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    # In a real app we'd save it and run inference. Here we just return mock JSON.
    return jsonify(mock_ai_detection("dummy_path"))

@app.route('/api/reports', methods=['GET'])
def get_reports():
    email = request.args.get('email')
    query = Report.query
    if email:
        query = query.filter_by(email=email)
    reports = query.order_by(Report.report_time.desc()).all()
    return jsonify([r.to_dict() for r in reports])

@app.route('/api/reports/<int:id>/status', methods=['PUT'])
def update_status(id):
    report = Report.query.get_or_404(id)
    data = request.json
    if 'status' in data:
        report.status = data['status']
        db.session.commit()
        return jsonify({'message': 'Status updated', 'report': report.to_dict()})
    return jsonify({'error': 'No status provided'}), 400

@app.route('/api/track/<report_id>', methods=['GET'])
def track_report(report_id):
    report = Report.query.filter_by(report_id=report_id).first()
    if report:
        return jsonify(report.to_dict())
    return jsonify({'error': 'Report not found'}), 404

@app.route('/api/certificate/<report_id>', methods=['GET'])
def generate_certificate(report_id):
    report = Report.query.filter_by(report_id=report_id).first()
    if not report:
        return jsonify({'error': 'Report not found'}), 404
        
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Draw simple certificate
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width / 2.0, height - 100, "Certificate of Appreciation")
    
    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2.0, height - 150, "Presented to")
    
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2.0, height - 200, report.name)
    
    text = f"For contributing to a safer community by reporting road damage on {report.report_time.strftime('%Y-%m-%d')}."
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2.0, height - 250, text)
    
    c.drawCentredString(width / 2.0, height - 300, f"Report ID: {report.report_id}")
    
    c.showPage()
    c.save()
    
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"Certificate_{report_id}.pdf",
        mimetype='application/pdf'
    )

if __name__ == '__main__':
    app.run(debug=True, port=5000)
