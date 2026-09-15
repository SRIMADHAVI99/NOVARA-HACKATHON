# 🚧 InfraScanAI — Computer Vision Road Damage Monitoring Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)](https://flask.palletsprojects.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-red.svg)](https://opencv.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](#license)

**InfraScanAI** is an automated road damage detection and infrastructure monitoring system. It allows citizens to submit road damage reports via desktop or mobile devices, uses an algorithmic **Computer Vision engine** (OpenCV + NumPy) to detect potholes, cracks, and road surface anomalies, and provides municipal authorities with an interactive dashboard for maintenance tracking.

---

## 📌 Overview

Municipal road maintenance relies on manual inspections and citizen complaints. **InfraScanAI** streamlines this process by:
1. Extracting visual pixel features (dark cavity contours, fracture line density, texture variance) from user-uploaded imagery.
2. Estimating damage category (**Pothole**, **Crack**, or **No Damage**), confidence score, and severity level (**High**, **Medium**, **Low**, **None**).
3. Mapping geographical report locations with interactive maps (Leaflet/OpenStreetMap fallback with optional Google Maps API integration).
4. Generating formal PDF **Certificates of Appreciation** for citizen contributors.

> ℹ️ **Current Architecture Note**: The current version operates as an algorithmic **Computer Vision prototype** utilizing feature-extraction heuristics (OpenCV/NumPy). For commercial production deployments, a deep convolutional neural network (e.g., **YOLOv8** fine-tuned on RDD datasets) can replace or complement the current engine.

---

## 🛠️ Tech Stack

### Backend
- **Python 3.10+** & **Flask 3.0**
- **Flask-SQLAlchemy** (SQLite Database)
- **ReportLab** (PDF Certificate Generation)
- **Werkzeug** (Secure File Upload Handling)

### Computer Vision & Analytics
- **OpenCV 4.x** (Image Processing & Matrix Operations)
- **NumPy** (Pixel Feature Mathematics & Thresholding)

### Frontend & Visualization
- **HTML5**, **Vanilla CSS3** (Civic Theme Design System)
- **JavaScript (ES6+)**
- **Leaflet.js & OpenStreetMap** (Default Interactive Mapping)
- **Google Maps JavaScript API** (Optional Cloud Integration via `.env`)
- **Chart.js** (Dashboard Analytics)

---

## 🤖 Computer Vision Pipeline

```text
               Uploaded Image (JPG / PNG / WEBP)
                              │
                              ▼
                Standardized Resizing (400x400)
                              │
               ┌──────────────┴──────────────┐
               ▼                             ▼
   Dark Cavity & Blob Analysis    Edge & Fracture Analysis
   (Luminance Thresholding +      (Gaussian Blur + Canny Edges
    Contour Max Area Ratio)        + Sobel Gradient Magnitude)
               │                             │
               └──────────────┬──────────────┘
                              ▼
            Feature-Based Scoring & Classification
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
      Pothole               Crack              No Damage
   (Dark Pit Shadows)  (Linear Edges)     (Uniform Pavement)
```

1. **Preprocessing**: Uploaded images are validated for corrupt byte structures and normalized to $400 \times 400$ grayscale matrices.
2. **Pothole Detection**:
   - Computes dynamic dark-pixel thresholding ($I < 0.65 \times \bar{I}$).
   - Extracts connected component contours (`cv2.findContours`) and measures relative cavity area (`max_contour_ratio`).
3. **Crack Detection**:
   - Applies Gaussian smoothing followed by Canny edge detection and Sobel gradient magnitude filtering ($|\nabla I| = \sqrt{I_x^2 + I_y^2}$).
   - Evaluates high-contrast fracture line density (`edge_density` & `gradient_ratio`).
4. **Undamaged Pavement**:
   - Evaluates surface texture variance ($\sigma$). Uniform surfaces with low edge density and no dark cavities are classified as *No Damage*.

---

## 📂 Project Structure

```text
NOVARA-HACKATHON/
├── InfraScanAI/
│   ├── app.py                 # Flask server, API routes & CV engine
│   ├── models.py              # SQLAlchemy database schemas
│   ├── requirements.txt       # Python dependencies
│   ├── run.bat                # Windows quick launcher
│   ├── .env.example           # Environment variables template
│   ├── static/
│   │   ├── css/style.css      # Custom styling & responsive layouts
│   │   └── js/
│   │       ├── main.js        # Citizen flow & location detection
│   │       └── admin.js       # Dashboard, map & status updates
│   ├── templates/
│   │   ├── base.html          # Layout template with Leaflet fallback
│   │   ├── index.html         # Portal role selector
│   │   ├── citizen_login.html # Citizen entry form
│   │   ├── report.html        # Damage report & image upload
│   │   ├── result.html        # CV analysis result & insights
│   │   ├── my_reports.html    # Citizen report history
│   │   ├── officer_login.html # Officer access gateway
│   │   └── admin.html         # Admin command center & analytics
│   ├── tests/
│   │   └── test_suite.py      # Unit & integration test suite
│   ├── uploads/               # Stored report images (.gitkeep)
│   └── certificates/          # Generated PDF certificates (.gitkeep)
├── .gitignore                 # Secrets, DB & temporary file rules
└── README.md                  # Project documentation
```

---

## ⚡ Quick Start & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/SRIMADHAVI99/NOVARA-HACKATHON.git
cd NOVARA-HACKATHON/InfraScanAI
```

### 2. Set Up Virtual Environment & Dependencies
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Environment Variables (Optional)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
To enable Google Maps cloud tiles, set `GOOGLE_MAPS_API_KEY=your_key_here` in `.env`. If left empty, **Leaflet/OpenStreetMap** will automatically serve interactive maps without requiring API keys.

### 4. Run the Application
```bash
python app.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your web browser.

---

## 🧪 Testing

Run the automated unittest suite (tests CV feature classification, upload security, database persistence, and PDF generation):
```bash
python -m unittest tests/test_suite.py
```

---

## 🔒 Security Features

- **Strict File Type Validation**: Enforces extensions (`.png`, `.jpg`, `.jpeg`, `.webp`) and verifies actual image decodability using OpenCV.
- **Upload Size Limit**: Restricts request payload to 16 MB (`MAX_CONTENT_LENGTH`).
- **Filename Sanitization**: Applies `werkzeug.utils.secure_filename` with UUID prefixes to prevent path traversal.
- **Secrets Management**: Excludes `.env` credentials, database binaries, and temporary files via `.gitignore`.

---

## 🚀 Future Scope

- **Deep Learning Upgrade**: Integrate a YOLOv8 / Faster R-CNN object detector trained on global road damage benchmarks (RDD2022).
- **Mobile Native App**: Build an offline-first React Native / Flutter app for field inspectors.
- **Automated Work-Order Dispatch**: Connect repaired reports directly to municipal department ticketing systems.

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for details.
