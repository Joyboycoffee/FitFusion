import os
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_cors import CORS
import numpy as np
import tensorflow as tf
import bcrypt
import jwt
import pymongo
import datetime

# 🔹 Setup Flask App with Correct Paths
BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # Backend directory path
TEMPLATES_DIR = os.path.join(BASE_DIR, "../frontend/Templates")
STATIC_DIR = os.path.join(BASE_DIR, "../frontend/Static")

app = Flask(
    __name__,
    template_folder=TEMPLATES_DIR,  # Ensures Flask finds templates
    static_folder=STATIC_DIR
)
CORS(app)
app.config["SECRET_KEY"] = "secretkey"

# 🔹 Connect to MongoDB
try:
    from pymongo import MongoClient
    client = MongoClient("mongodb://localhost:27017/")
    db = client["FitFusion"]
    users = db["users"]
    print("✅ Connected to MongoDB successfully!")
except Exception as e:
    print(f"❌ Error connecting to MongoDB: {e}")
    users = None  # Prevents crashes if MongoDB fails

# 🔹 Load the AI Model
try:
    model_path = os.path.join(BASE_DIR, "../ai_model/body_model.h5")  # Use absolute path
    model = tf.keras.models.load_model(model_path)
    print("✅ Model loaded successfully!")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    model = None  # Prevents crashes if the model fails to load

# 🔹 Serve Frontend (Home Page)
@app.route("/")
def home():
    return render_template("index.html")  # Loads frontend correctly

# 🔹 Signup API

@app.route("/signup", methods=["POST"])
def signup():
    if users is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        # 🔹 Ensure JSON is properly received
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data received"}), 400

        # 🔹 Extract fields safely
        name = data.get("name")
        email = data.get("email")
        password = data.get("password")

        # 🔹 Validate fields
        if not name or not email or not password:
            return jsonify({"error": "Missing name, email, or password"}), 400

        # 🔹 Check if the user already exists
        existing_user = users.find_one({"email": email})
        if existing_user:
            return jsonify({"error": "User already exists"}), 409

        # 🔹 Hash password securely
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        # 🔹 Store user in database
        users.insert_one({"name": name, "email": email, "password": hashed_password})

        print(f"✅ New User Registered: {name} ({email})")  # Debugging print statement

        return jsonify({"message": "User registered successfully!"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 🔹 Login API
@app.route("/login", methods=["POST"])
def login():
    if users is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        data = request.get_json
        if not data or "email" not in data or "password" not in data:
            return jsonify({"error": "Missing email or password"}), 400

        user = users.find_one({"email": data["email"]})
        if user:
            print(f"🔍 Checking User: {user['email']}")  # Debugging print statement

        if user and bcrypt.checkpw(data["password"].encode("utf-8"), user["password"]):
            token = jwt.encode(
                {"email": data["email"], "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)},
                app.config["SECRET_KEY"],
                algorithm="HS256"
            )
            print(f"✅ User Logged In: {data['email']}")  # Debugging print statement
            return jsonify({"token": token})

        print(f"❌ Login Failed for: {data['email']}")  # Debugging print statement
        return jsonify({"error": "Invalid credentials"}), 401

    except Exception as e:
        return jsonify({"error": str(e)}), 500




# 🔹 AI Model Prediction API
@app.route("/predict", methods=["POST"])
def predict():
    if model is None:
        return jsonify({"error": "Model not found or failed to load"}), 500

    try:
        data = request.json
        if "height" not in data or "weight" not in data:
            return jsonify({"error": "Missing height or weight"}), 400

        height = float(data['height'])
        weight = float(data['weight'])

        # Preprocessing input
        input_data = np.array([[height, weight]])

        # Predict body type
        prediction = model.predict(input_data)
        predicted_class = np.argmax(prediction)  # Assuming multi-class classification

        body_types = ["Ectomorph", "Mesomorph", "Endomorph"]
        result = body_types[predicted_class] if predicted_class < len(body_types) else "Unknown"

        return jsonify({"body_type": result})

    except Exception as e:
        return jsonify({"error": str(e)}), 400

# 🔹 Profile Route (Protected)
@app.route("/profile")
def profile():
    token = request.args.get("token")
    if not token:
        return redirect(url_for("home"))

    try:
        decoded_token = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        user = users.find_one({"email": decoded_token["email"]})
        if user:
            return jsonify({"email": user["email"], "message": "Welcome to your profile!"})

    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Session expired, please login again"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    return redirect(url_for("home"))

# 🔹 Logout (Clears session)
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# 🔹 Run Flask App
if __name__ == "__main__":
    app.run(debug=True)

print(app.url_map)
