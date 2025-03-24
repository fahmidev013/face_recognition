# Backend: face_recognition_api.py
from flask import Flask, request, jsonify
import numpy as np
import cv2
import face_recognition
from PIL import Image
from sklearn.ensemble import IsolationForest
import datetime
import os
import requests
import mysql.connector

app = Flask(__name__)

KNOWN_FACES_DIR = "known_faces"
os.makedirs(KNOWN_FACES_DIR, exist_ok=True)

def init_db():
    conn = mysql.connector.connect(
        host="localhost",
        port=3307,
        user="root",
        password="admin123",
        database="face_recognition"
    )
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(255),
                        timestamp DATETIME,
                        ip_address VARCHAR(255),
                        device_info VARCHAR(255)
                      )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(255),
                        image_path VARCHAR(255)
                      )''')
    conn.commit()
    conn.close()

init_db()


known_face_encodings = []
known_face_names = []

def load_known_faces():
    global known_face_encodings, known_face_names
    conn = mysql.connector.connect(
        host="localhost",
        port=3307,
        user="root",
        password="admin123",
        database="face_recognition"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT name, image_path FROM users")
    users = cursor.fetchall()
    conn.close()

    for name, img_path in users:
        image = face_recognition.load_image_file(img_path)
        encoding = face_recognition.face_encodings(image)
        if encoding:
            known_face_encodings.append(encoding[0])
            known_face_names.append(name)

load_known_faces()

@app.route("/register", methods=["POST"])
def register():
    name = request.form.get("name")
    file = request.files["image"]
    if not name or not file:
        return jsonify({"message": "Name and image file are required."}), 400

    image = Image.open(file)
    image = image.convert("RGB")
    image_path = os.path.join(KNOWN_FACES_DIR, f"{name}.jpg")
    image.save(image_path)

    conn = mysql.connector.connect(
        host="localhost",
        port=3307,
        user="root",
        password="admin123",
        database="face_recognition"
    )
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (name, image_path) VALUES (%s, %s)", (name, image_path))
    conn.commit()
    conn.close()

    load_known_faces()  # Refresh known faces

    return jsonify({"message": f"User {name} registered successfully."}), 200


def log_activity(name, ip_address, device_info):
    conn = mysql.connector.connect(
        host="localhost",
        port=3307,
        user="root",
        password="admin123",
        database="face_recognition"
    )
    cursor = conn.cursor()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO logs (name, timestamp, ip_address, device_info) VALUES (%s, %s, %s, %s)", 
                   (name, timestamp, ip_address, device_info))
    conn.commit()
    conn.close()


def is_live_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    return laplacian_var > 100


def detect_anomaly(face_encodings):
    if len(face_encodings) < 5:
        return False
    model = IsolationForest(contamination=0.1)
    model.fit(face_encodings)
    anomaly_scores = model.predict([face_encodings[-1]])
    return anomaly_scores[0] == -1


@app.route("/recognize", methods=["POST"])
def recognize():
    file = request.files["image"]
    image = Image.open(file)
    image = image.convert("RGB")
    image = np.array(image)

    face_encodings = face_recognition.face_encodings(image)

    if not face_encodings:
        return jsonify({"message": "No face detected"}), 400

    matches = face_recognition.compare_faces(known_face_encodings, face_encodings[0])
    name = "Unknown"
    if True in matches:
        first_match_index = matches.index(True)
        name = known_face_names[first_match_index]

    log_activity(name, request.remote_addr, request.headers.get('User-Agent'))
    return jsonify({"name": name})


if __name__ == "__main__":
    app.run(debug=True)
