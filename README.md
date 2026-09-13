# 🚧 InfraScanAI

AI-powered road damage detection and infrastructure monitoring system designed to identify road conditions and help authorities monitor and manage damaged road infrastructure.

---

## 📌 Overview

InfraScanAI is an AI-driven infrastructure monitoring platform that uses computer vision to detect road damage from images.

The system helps identify damaged road sections, visualize their locations, and provide an administrative interface for monitoring infrastructure conditions.

---

## 💡 Features

### 🤖 AI-Powered Road Damage Detection

- Detects road damage from uploaded images
- Uses computer vision / machine learning
- Identifies damaged road areas
- Provides detection results for infrastructure monitoring

### 🗺️ Location Visualization

- Google Maps integration
- Displays reported/detected road damage locations
- Helps visualize affected areas geographically

### 📊 Admin Dashboard

- Monitor reported road damage
- View detection results
- Track infrastructure issues
- Manage reported locations

### 📷 Image-Based Analysis

- Upload road images
- Process images through the AI detection system
- Display detection results through the web interface

---

## 🛠️ Tech Stack

### Frontend

- HTML
- CSS
- JavaScript

### Backend

- Python
- Flask

### AI / Machine Learning

- Computer Vision
- Machine Learning
- Image Processing

### Maps

- Google Maps API

---

## 🏗️ System Architecture

```text
User
  │
  ▼
Web Interface
  │
  ▼
Flask Backend
  │
  ├──────────────► AI Road Damage Detection
  │
  ├──────────────► Image Processing
  │
  └──────────────► Google Maps
                       │
                       ▼
                Location Visualization
                       │
                       ▼
                 Admin Dashboard
```
