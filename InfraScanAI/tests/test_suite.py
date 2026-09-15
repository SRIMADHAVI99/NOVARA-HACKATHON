import unittest
import os
import sys
import io
import cv2
import numpy as np

# Ensure InfraScanAI root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db, cv_damage_detection, allowed_file, Report

class InfraScanAITestSuite(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        cls.client = app.test_client()
        with app.app_context():
            db.create_all()

        # Create temporary test fixtures directory
        cls.fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures')
        os.makedirs(cls.fixtures_dir, exist_ok=True)

        # 1. Normal Road Fixture
        cls.normal_img_path = os.path.join(cls.fixtures_dir, 'normal_road.jpg')
        normal_road = np.full((400, 400, 3), 130, dtype=np.uint8)
        noise = np.random.randint(-10, 10, (400, 400, 3), dtype=np.int16)
        normal_road = np.clip(normal_road.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        cv2.imwrite(cls.normal_img_path, normal_road)

        # 2. Crack Road Fixture
        cls.crack_img_path = os.path.join(cls.fixtures_dir, 'crack_road.jpg')
        crack_road = normal_road.copy()
        points = np.array([[50, 100], [120, 150], [180, 140], [250, 220], [320, 300]], np.int32)
        cv2.polylines(crack_road, [points], isClosed=False, color=(20, 20, 20), thickness=4)
        cv2.imwrite(cls.crack_img_path, crack_road)

        # 3. Pothole Road Fixture
        cls.pothole_img_path = os.path.join(cls.fixtures_dir, 'pothole_road.jpg')
        pothole_road = normal_road.copy()
        cv2.ellipse(pothole_road, (200, 200), (90, 60), 15, 0, 360, (20, 15, 15), -1)
        cv2.imwrite(cls.pothole_img_path, pothole_road)

        # 4. Small Image Fixture
        cls.small_img_path = os.path.join(cls.fixtures_dir, 'small_road.jpg')
        small_road = np.full((50, 50, 3), 120, dtype=np.uint8)
        cv2.imwrite(cls.small_img_path, small_road)

        # 5. Blank White Image Fixture
        cls.blank_white_path = os.path.join(cls.fixtures_dir, 'blank_white.jpg')
        blank_white = np.full((400, 400, 3), 255, dtype=np.uint8)
        cv2.imwrite(cls.blank_white_path, blank_white)

        # 6. Pitch Black Image Fixture
        cls.pitch_black_path = os.path.join(cls.fixtures_dir, 'pitch_black.jpg')
        pitch_black = np.full((400, 400, 3), 5, dtype=np.uint8)
        cv2.imwrite(cls.pitch_black_path, pitch_black)

        # 7. Corrupt File Fixture
        cls.corrupt_img_path = os.path.join(cls.fixtures_dir, 'corrupt.jpg')
        with open(cls.corrupt_img_path, 'wb') as f:
            f.write(b"not an image file content")

    def test_allowed_file(self):
        self.assertTrue(allowed_file("road.jpg"))
        self.assertTrue(allowed_file("image.png"))
        self.assertTrue(allowed_file("photo.webp"))
        self.assertFalse(allowed_file("script.py"))
        self.assertFalse(allowed_file("malicious.exe"))

    def test_cv_engine_normal_road(self):
        res = cv_damage_detection(self.normal_img_path)
        self.assertEqual(res['status'], 'success')
        self.assertEqual(res['damage_type'], 'No Damage')
        self.assertEqual(res['severity'], 'None')
        self.assertGreaterEqual(res['confidence'], 0.80)

    def test_cv_engine_pothole(self):
        res = cv_damage_detection(self.pothole_img_path)
        self.assertEqual(res['status'], 'success')
        self.assertEqual(res['damage_type'], 'Pothole')
        self.assertIn(res['severity'], ['Medium', 'High'])
        self.assertGreaterEqual(res['confidence'], 0.75)

    def test_cv_engine_crack(self):
        res = cv_damage_detection(self.crack_img_path)
        self.assertEqual(res['status'], 'success')
        self.assertIn(res['damage_type'], ['Crack', 'Pothole'])

    def test_cv_engine_blank_white(self):
        res = cv_damage_detection(self.blank_white_path)
        self.assertEqual(res['status'], 'success')
        self.assertEqual(res['damage_type'], 'No Damage')
        self.assertEqual(res['severity'], 'None')
        self.assertEqual(res['confidence'], 0.65)

    def test_cv_engine_pitch_black(self):
        res = cv_damage_detection(self.pitch_black_path)
        self.assertEqual(res['status'], 'success')
        self.assertEqual(res['damage_type'], 'No Damage')
        self.assertEqual(res['severity'], 'None')
        self.assertEqual(res['confidence'], 0.65)

    def test_cv_engine_small_image(self):
        res = cv_damage_detection(self.small_img_path)
        self.assertEqual(res['status'], 'success')

    def test_cv_engine_corrupt_file(self):
        res = cv_damage_detection(self.corrupt_img_path)
        self.assertEqual(res['status'], 'error')
        self.assertIsNone(res['damage_type'])
        self.assertIsNone(res['severity'])
        self.assertIsNone(res['confidence'])
        self.assertIn('Could not decode', res['message'])

    def test_api_corrupt_image_upload_rejected(self):
        data = {
            'name': 'Corrupt Tester',
            'email': 'corrupt@example.com',
            'latitude': '37.7749',
            'longitude': '-122.4194',
            'image': (io.BytesIO(b"corrupt image payload bytes"), "corrupt.jpg")
        }
        res = self.client.post('/api/report', data=data, content_type='multipart/form-data')
        self.assertEqual(res.status_code, 400)
        json_resp = res.get_json()
        self.assertIn('error', json_resp)
        self.assertIn('corrupted or not a valid image', json_resp['error'])

    def test_api_invalid_extension(self):
        data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'latitude': '37.7749',
            'longitude': '-122.4194',
            'image': (io.BytesIO(b"data"), "test.txt")
        }
        res = self.client.post('/api/report', data=data, content_type='multipart/form-data')
        self.assertEqual(res.status_code, 400)
        self.assertIn('Invalid file type', res.get_json()['error'])

    def test_api_valid_submission_and_flow(self):
        with open(self.pothole_img_path, 'rb') as img_f:
            data = {
                'name': 'John Doe',
                'email': 'john@example.com',
                'phone': '1234567890',
                'latitude': '37.7749',
                'longitude': '-122.4194',
                'notes': 'Deep pothole',
                'image': (img_f, 'pothole_upload.jpg')
            }
            res = self.client.post('/api/report', data=data, content_type='multipart/form-data')

        self.assertEqual(res.status_code, 201)
        json_data = res.get_json()
        report_id = json_data['report_id']
        self.assertTrue(report_id.startswith("REP-"))
        self.assertEqual(json_data['detection']['damage_type'], 'Pothole')

        # Track Report
        track_res = self.client.get(f'/api/track/{report_id}')
        self.assertEqual(track_res.status_code, 200)
        self.assertEqual(track_res.get_json()['name'], 'John Doe')

        # Status Update
        db_id = track_res.get_json()['id']
        update_res = self.client.put(f'/api/reports/{db_id}/status', json={'status': 'Under Review'})
        self.assertEqual(update_res.status_code, 200)
        self.assertEqual(update_res.get_json()['report']['status'], 'Under Review')

        # Generate Certificate
        cert_res = self.client.get(f'/api/certificate/{report_id}')
        self.assertEqual(cert_res.status_code, 200)
        self.assertEqual(cert_res.headers['Content-Type'], 'application/pdf')

    def test_api_certificate_not_found(self):
        res = self.client.get('/api/certificate/REP-NONEXISTENT')
        self.assertEqual(res.status_code, 404)

if __name__ == '__main__':
    unittest.main()
