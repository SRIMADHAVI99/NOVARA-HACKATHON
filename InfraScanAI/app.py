from flask import Flask, request, jsonify, send_file, render_template, send_from_directory
from flask_cors import CORS
import os
import uuid
import random
from datetime import datetime, timezone
from models import db, Report
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# Database Setup
basedir = os.path.abspath(os.path.dirname(__name__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# File uploads & Security config
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max limit

UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
CERT_FOLDER = os.path.join(basedir, 'certificates')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CERT_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db.init_app(app)

with app.app_context():
    db.create_all()

@app.context_processor
def inject_google_maps_key():
    return dict(google_maps_api_key=os.environ.get('GOOGLE_MAPS_API_KEY', ''))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

import cv2
import numpy as np

# --- Computer Vision AI Detection Function ---
def cv_damage_detection(image_path):
    """
    Computer Vision Road Damage Classifier using pixel feature analysis:
    - Dark Cavity / Contour Analysis for Potholes
    - Canny Edge Density & Sobel Gradient Magnitude for Cracks
    - Pixel Brightness & Texture Variation Analysis for Undamaged Roads
    - Feature Quality Check for low-information / blank / extreme luminance images
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            return {
                'status': 'error',
                'damage_type': 'No Damage',
                'severity': 'None',
                'confidence': 0.50,
                'message': 'Could not decode image file.'
            }

        # Resize for standardized pixel feature analysis
        img_resized = cv2.resize(img, (400, 400))
        gray = cv2.cvtColor(img_resized, cv2.COLOR_BGR2GRAY)
        total_pixels = 400 * 400
        mean_val = float(np.mean(gray))
        std_dev = float(np.std(gray))

        # Check for uninformative / featureless / blank / extreme luminance images
        is_low_info = (std_dev < 4.0) or (mean_val > 245.0) or (mean_val < 15.0)

        # 1. Dark Cavity Blob Analysis (Potholes produce pit shadows relative to surface brightness)
        if mean_val < 15.0 or mean_val > 245.0:
            dark_threshold = 0.0
        else:
            dark_threshold = max(35.0, mean_val * 0.65)

        dark_mask = (gray < dark_threshold).astype(np.uint8) * 255 if dark_threshold > 0 else np.zeros((400, 400), dtype=np.uint8)
        dark_pixel_ratio = float(np.count_nonzero(dark_mask) / total_pixels)

        contours, _ = cv2.findContours(dark_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        max_contour_area = max([cv2.contourArea(c) for c in contours]) if contours else 0.0
        max_contour_ratio = float(max_contour_area / total_pixels)

        # 2. Edge & Gradient Analysis (Cracks produce linear high-contrast edges)
        blur = cv2.GaussianBlur(gray, (3, 3), 0)
        edges = cv2.Canny(blur, 30, 90)
        edge_density = float(np.count_nonzero(edges) / total_pixels)

        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        sobel_mag = np.sqrt(sobelx**2 + sobely**2)
        gradient_ratio = float(np.count_nonzero(sobel_mag > 80) / total_pixels)

        # 3. Decision Rules Based on Extracted Features
        if max_contour_ratio > 0.025 or (dark_pixel_ratio > 0.08 and max_contour_ratio > 0.015):
            damage_type = 'Pothole'
            confidence = min(0.96, max(0.78, 0.76 + max_contour_ratio * 2.5 + dark_pixel_ratio * 0.5))
            if max_contour_ratio > 0.08 or dark_pixel_ratio > 0.22:
                severity = 'High'
            elif max_contour_ratio > 0.04 or dark_pixel_ratio > 0.12:
                severity = 'Medium'
            else:
                severity = 'Low'
        elif edge_density > 0.005 or gradient_ratio > 0.02:
            damage_type = 'Crack'
            confidence = min(0.94, max(0.72, 0.70 + (edge_density + gradient_ratio) * 3.0))
            if edge_density > 0.05 or gradient_ratio > 0.08:
                severity = 'High'
            elif edge_density > 0.02 or gradient_ratio > 0.04:
                severity = 'Medium'
            else:
                severity = 'Low'
        else:
            damage_type = 'No Damage'
            severity = 'None'
            if is_low_info:
                # Low visual detail / featureless blank / overexposed image gets moderate detection confidence
                confidence = 0.65
            else:
                confidence = min(0.98, max(0.82, 0.95 - (edge_density + gradient_ratio) * 2.0))

        return {
            'status': 'success',
            'damage_type': damage_type,
            'severity': severity,
            'confidence': round(confidence, 2),
            'message': f'Computer Vision analysis complete. Analyzed pixel gradients, dark cavity ratio ({dark_pixel_ratio:.2f}), and edge density ({edge_density:.2f}).'
        }

    except Exception as e:
        return {
            'status': 'error',
            'damage_type': 'No Damage',
            'severity': 'None',
            'confidence': 0.50,
            'message': f'CV processing exception: {str(e)}'
        }

# Alias for backward compatibility
mock_ai_detection = cv_damage_detection

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

    if not allowed_file(image.filename):
        return jsonify({'error': 'Invalid file type. Allowed formats: PNG, JPG, JPEG, WEBP.'}), 400

    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone', '')
    notes = request.form.get('notes', '')
    latitude = form_float(request.form.get('latitude'))
    longitude = form_float(request.form.get('longitude'))
    
    if not name or not email or latitude is None or longitude is None:
        return jsonify({'error': 'Missing required fields'}), 400

    # Save image securely
    safe_name = secure_filename(image.filename)
    filename = f"{uuid.uuid4().hex}_{safe_name}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image.save(filepath)

    # Validate image decoding with OpenCV
    test_img = cv2.imread(filepath)
    if test_img is None:
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'error': 'Uploaded file is corrupted or not a valid image'}), 400

    # Call CV Detection
    detection_result = cv_damage_detection(filepath)

    # Create Report
    report_id = f"REP-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{random.randint(100, 999)}"
    
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
def standalone_detect():
    """Standalone endpoint for Computer Vision road damage detection"""
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    image = request.files['image']
    if image.filename == '' or not allowed_file(image.filename):
        return jsonify({'error': 'Invalid image file'}), 400
    
    safe_name = secure_filename(image.filename)
    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{uuid.uuid4().hex}_{safe_name}")
    image.save(temp_path)
    
    result = cv_damage_detection(temp_path)
    if os.path.exists(temp_path):
        os.remove(temp_path)
        
    return jsonify(result)

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
    report = db.session.get(Report, id)
    if not report:
        return jsonify({'error': 'Report not found'}), 404
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
