import os
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, make_response
from flask_cors import CORS
import numpy as np
import tensorflow as tf
import bcrypt
import jwt
import pymongo
import datetime
import functools  # Add this with your other imports

# Setup Flask App
BASE_DIR = os.path.abspath(os.path.dirname(__file__))  
TEMPLATES_DIR = os.path.join(BASE_DIR, "../frontend/Templates")
STATIC_DIR = os.path.join(BASE_DIR, "../frontend/Static")

app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)
CORS(app)
app.config["SECRET_KEY"] = os.urandom(24).hex()

# Connect to MongoDB
try:
    client = pymongo.MongoClient("mongodb+srv://fitfusiondatabase:HhkXTWFoAkaYXyVK@joyboy.pevs1.mongodb.net/FitFusion?retryWrites=true&w=majority&appName=joyboy")
    db = client["FitFusion"]
    users = db["users"]
    print("✅ Connected to MongoDB Atlas successfully!")
except Exception as e:
    print(f"❌ Error connecting to MongoDB Atlas: {e}")
    users = None

# Load AI Model
try:
    model_path = os.path.join(BASE_DIR, "../ai_model/body_model.h5")
    model = tf.keras.models.load_model(model_path)
    print("✅ Model loaded successfully!")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    model = None

# Helper Function to Generate JWT Token
def generate_jwt(email):
    payload = {
        "email": email,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    return jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")

# Middleware to Protect Routes
# Update the token_required decorator
def token_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get("token")
        if not token:
            return redirect(url_for("home"))
        try:
            jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Session expired, please login again"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid session"}), 401
        return f(*args, **kwargs)
    return decorated

# Routes
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/forgot_password")
def forgot_password_page():
    return render_template("forgot_password.html")

@app.route("/signup", methods=["POST"])
def signup():
    if users is None:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data received"}), 400
        name, email, password = data.get("name"), data.get("email"), data.get("password")
        if not name or not email or not password:
            return jsonify({"error": "Missing name, email, or password"}), 400
        if users.find_one({"email": email}):
            return jsonify({"error": "User already exists"}), 409
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        user_data = {
            "name": name,
            "email": email,
            "password": hashed_password,
            "age": None,
            "gender": None,
            "height": None,  # in cm
            "weight": None,  # in kg
            "fitness_goal": None,  # weight_loss, muscle_gain, maintenance
            "activity_level": None,  # sedentary, light, moderate, active, very_active
            "dietary_preference": None,  # vegetarian, vegan, omnivore, pescatarian
            "allergies": [],
            "created_at": datetime.datetime.utcnow(),
            "updated_at": datetime.datetime.utcnow()
        }
        users.insert_one(user_data)
        return jsonify({"message": "User registered successfully!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/login", methods=["POST"])
def login():
    if users is None:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        data = request.get_json()
        if not data or "email" not in data or "password" not in data:
            return jsonify({"error": "Missing email or password"}), 400
        
        user = users.find_one({"email": data["email"]})
        if user and bcrypt.checkpw(data["password"].encode("utf-8"), user["password"].encode("utf-8")):
            token = generate_jwt(user["email"])
            
            # Proper JSON response with token
            resp = make_response(jsonify({"message": "Login successful", "redirect": "/dashboard/new"}))
            resp.set_cookie("token", token, httponly=True)
            return resp
        
        return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/dashboard')
@token_required
def dashboard():
    resp = make_response(render_template('dashboard_new.html'))
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return resp

@app.route('/dashboard/new')
@token_required
def new_dashboard():
    return render_template('dashboard_new.html')

@app.route("/predict", methods=["POST"])
def predict():
    if model is None:
        return jsonify({"error": "Model not found"}), 500
    try:
        data = request.json
        if "height" not in data or "weight" not in data:
            return jsonify({"error": "Missing height or weight"}), 400
        height, weight = float(data['height']), float(data['weight'])
        prediction = model.predict(np.array([[height, weight]]))
        result = ["Ectomorph", "Mesomorph", "Endomorph"][np.argmax(prediction)]
        return jsonify({"body_type": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/profile', methods=['GET'])
@token_required
def get_profile():
    try:
        token = request.cookies.get('token')
        decoded_token = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        user = users.find_one({"email": decoded_token["email"]}, {"password": 0})
        
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        # Convert ObjectId to string for JSON serialization
        user['_id'] = str(user['_id'])
        resp = make_response(jsonify(user))
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        return resp
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/profile', methods=['PUT'])
@token_required
def update_profile():
    try:
        token = request.cookies.get('token')
        decoded_token = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        data = request.json
        
        # Update only the fields that are provided in the request
        update_data = {}
        
        # Personal Information
        if 'name' in data:
            update_data['name'] = data['name']
        if 'age' in data:
            update_data['age'] = int(data['age']) if data['age'] else None
        if 'gender' in data:
            update_data['gender'] = data['gender']
            
        # Body Measurements
        if 'height' in data and data['height']:
            update_data['height'] = float(data['height'])  # in cm
        if 'weight' in data and data['weight']:
            update_data['weight'] = float(data['weight'])  # in kg
            
        # Fitness Goals
        if 'fitness_goal' in data:
            update_data['fitness_goal'] = data['fitness_goal']
        if 'activity_level' in data:
            update_data['activity_level'] = data['activity_level']
        # Dashboard Goal Progress Type
        if 'dashboard_goal_type' in data:
            update_data['dashboard_goal_type'] = data['dashboard_goal_type']
            
        # Dietary Preferences
        if 'dietary_preference' in data:
            update_data['dietary_preference'] = data['dietary_preference']
        if 'allergies' in data and isinstance(data['allergies'], list):
            update_data['allergies'] = data['allergies']
            
        # Add updated_at timestamp
        update_data['updated_at'] = datetime.datetime.utcnow()
            
        # Update the user document
        result = users.update_one(
            {"email": decoded_token["email"]},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            return jsonify({"error": "User not found"}), 404
            
        return jsonify({"message": "Profile updated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/logout")
def logout():
    resp = make_response(redirect(url_for("login")))
    resp.set_cookie("token", "", expires=0, httponly=True, samesite='Lax')
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return resp

# Log workout
@app.route('/api/log_workout', methods=['POST'])
@token_required
def log_workout():
    token = request.cookies.get('token')
    decoded_token = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
    user = users.find_one({"email": decoded_token["email"]})
    if not user:
        return jsonify({"error": "User not found"}), 404
    data = request.json
    log = {
        "date": data.get("date"),
        "type": data.get("type"),
        "duration": data.get("duration"),
        "calories_burned": data.get("calories_burned")
    }
    users.update_one({"email": user["email"]}, {"$push": {"workout_logs": log}})
    return jsonify({"success": True})

# Log nutrition
@app.route('/api/log_nutrition', methods=['POST'])
@token_required
def log_nutrition():
    token = request.cookies.get('token')
    decoded_token = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
    user = users.find_one({"email": decoded_token["email"]})
    if not user:
        return jsonify({"error": "User not found"}), 404
    data = request.json
    log = {
        "date": data.get("date"),
        "meal": data.get("meal"),
        "calories": data.get("calories"),
        "protein": data.get("protein"),
        "carbs": data.get("carbs"),
        "fat": data.get("fat")
    }
    users.update_one({"email": user["email"]}, {"$push": {"nutrition_logs": log}})
    return jsonify({"success": True})

# Workouts timeseries (last 7 days)
@app.route('/api/workout_timeseries', methods=['GET'])
@token_required
def workout_timeseries():
    import datetime
    token = request.cookies.get('token')
    decoded_token = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
    user = users.find_one({"email": decoded_token["email"]})
    if not user:
        return jsonify({"error": "User not found"}), 404
    today = datetime.date.today()
    days = [(today - datetime.timedelta(days=i)).isoformat() for i in range(6,-1,-1)]
    logs = user.get("workout_logs", [])
    per_day = {d: 0 for d in days}
    for log in logs:
        if log.get("date") in per_day:
            per_day[log["date"]] += 1
    return jsonify({"labels": days, "data": [per_day[d] for d in days]})

# Nutrition timeseries (last 7 days - calories)
@app.route('/api/nutrition_timeseries', methods=['GET'])
@token_required
def nutrition_timeseries():
    import datetime
    token = request.cookies.get('token')
    decoded_token = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
    user = users.find_one({"email": decoded_token["email"]})
    if not user:
        return jsonify({"error": "User not found"}), 404
    today = datetime.date.today()
    days = [(today - datetime.timedelta(days=i)).isoformat() for i in range(6,-1,-1)]
    logs = user.get("nutrition_logs", [])
    per_day = {d: 0 for d in days}
    for log in logs:
        if log.get("date") in per_day:
            per_day[log["date"]] += int(log.get("calories", 0))
    return jsonify({"labels": days, "data": [per_day[d] for d in days]})

# Dashboard stats API
@app.route('/api/dashboard_stats', methods=['GET'])
@token_required
def dashboard_stats():
    try:
        token = request.cookies.get('token')
        decoded_token = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        user = users.find_one({"email": decoded_token["email"]})
        if not user:
            return jsonify({"error": "User not found"}), 404

        import datetime
        today = datetime.date.today()
        days = [(today - datetime.timedelta(days=i)).isoformat() for i in range(6,-1,-1)]
        # Workouts this week
        logs = user.get("workout_logs", [])
        workouts_this_week = sum(1 for log in logs if log.get("date") in days)
        # Calories consumed this week
        nlogs = user.get("nutrition_logs", [])
        calories_consumed = sum(int(log.get("calories", 0)) for log in nlogs if log.get("date") in days)
        # BMI (keep as before)
        height = user.get('height', 170)
        weight = user.get('weight', 65)
        bmi = round((weight / ((height / 100) ** 2)), 1) if height and weight else None
        # Goal progress logic based on dashboard_goal_type
        dashboard_goal_type = user.get('dashboard_goal_type', 'weight_loss')
        goal_progress = 0
        goal_pie = [0, 100]
        if dashboard_goal_type == 'weight_loss':
            # Example: weight loss progress = percent of weight lost toward goal
            start_weight = user.get('start_weight', weight)
            target_weight = user.get('target_weight', weight-5)
            if start_weight > target_weight:
                lost = max(0, start_weight - weight)
                total = max(1, start_weight - target_weight)
                goal_progress = round((lost / total) * 100, 1)
                goal_pie = [goal_progress, max(0, 100-goal_progress)]
        elif dashboard_goal_type == 'muscle_gain':
            # Example: muscle gain progress = percent of muscle gained toward goal
            start_weight = user.get('start_weight', weight)
            target_weight = user.get('target_weight', weight+5)
            if target_weight > start_weight:
                gained = max(0, weight - start_weight)
                total = max(1, target_weight - start_weight)
                goal_progress = round((gained / total) * 100, 1)
                goal_pie = [goal_progress, max(0, 100-goal_progress)]
        elif dashboard_goal_type == 'workouts':
            # Example: percent of weekly workout goal
            workout_goal = user.get('workout_goal', 5)
            goal_progress = min(100, round((workouts_this_week / workout_goal) * 100, 1)) if workout_goal else 0
            goal_pie = [goal_progress, max(0, 100-goal_progress)]
        elif dashboard_goal_type == 'calories':
            # Example: percent of weekly calorie goal
            calorie_goal = user.get('calorie_goal', 14000)  # e.g., 2000/day * 7
            goal_progress = min(100, round((calories_consumed / calorie_goal) * 100, 1)) if calorie_goal else 0
            goal_pie = [goal_progress, max(0, 100-goal_progress)]
        else:
            # Custom or fallback
            goal_progress = user.get('goal_progress', 60)
            goal_pie = [goal_progress, max(0, 100-goal_progress)]

        stats = {
            "workouts_this_week": workouts_this_week,
            "calories_consumed": calories_consumed,
            "bmi": bmi,
            "goal_progress": goal_progress,
            "goal_pie": goal_pie
        }
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Add these new endpoints to your existing app.py

@app.route("/generate_workout_plan", methods=["POST"])
@token_required
def generate_workout_plan():
    try:
        data = request.json
        goal = data.get('goal')
        experience = data.get('experience')
        
        # AI logic for workout plan generation
        # This is a placeholder - implement your AI model here
        workout_plan = {
            "weekly_plan": [
                {"day": "Monday", "exercises": ["Push-ups", "Squats"]},
                {"day": "Wednesday", "exercises": ["Pull-ups", "Lunges"]},
                {"day": "Friday", "exercises": ["Deadlifts", "Planks"]}
            ],
            "intensity": experience,
            "goal_focus": goal
        }
        
        return jsonify(workout_plan)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/generate_nutrition_plan", methods=["POST"])
@token_required
def generate_nutrition_plan():
    try:
        data = request.json
        goal = data.get('goal')
        restrictions = data.get('dietary_restrictions', [])
        
        # AI logic for nutrition plan generation
        # This is a placeholder - implement your AI model here
        nutrition_plan = {
            "daily_calories": 2000,
            "macros": {
                "protein": "150g",
                "carbs": "200g",
                "fats": "65g"
            },
            "meal_suggestions": [
                {"meal": "Breakfast", "options": ["Oatmeal with fruits", "Protein smoothie"]},
                {"meal": "Lunch", "options": ["Grilled chicken salad", "Quinoa bowl"]},
                {"meal": "Dinner", "options": ["Salmon with vegetables", "Tofu stir-fry"]}
            ]
        }
        
        return jsonify(nutrition_plan)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# --- Password Reset OTP Logic ---
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

reset_otps = {}  # email -> {'otp': str, 'expires': datetime}

# Set your sender email here:
SENDER_EMAIL = "fitfusion.noreply@gmail.com"
APP_PASSWORD = "xxbv dryn vcce zavs"  # Provided by user, keep this secret!

# Helper to send OTP email
def send_otp_email(to_email, otp):
    subject = "FitFusion Password Reset OTP"
    body = f"""
    <h2>Your FitFusion OTP</h2>
    <p>Your One Time Password (OTP) is: <b>{otp}</b></p>
    <p>This OTP is valid for 10 minutes.</p>
    <br><p>If you did not request this, please ignore this email.</p>
    """
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, APP_PASSWORD)
            smtp.sendmail(SENDER_EMAIL, to_email, msg.as_string())
    except Exception as e:
        print(f"[FitFusion] Failed to send OTP email: {e}")
        return False
    return True

@app.route('/api/request_reset', methods=['POST'])
def request_reset():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    if not email:
        return jsonify({'error': 'Email required'}), 400
    user = users.find_one({'email': email})
    if not user:
        return jsonify({'error': 'No user found with this email'}), 404
    otp = ''.join(random.choices(string.digits, k=6))
    expires = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
    reset_otps[email] = {'otp': otp, 'expires': expires}
    if not send_otp_email(email, otp):
        return jsonify({'error': 'Failed to send OTP email. Try again later.'}), 500
    return jsonify({'success': True, 'message': 'OTP sent to your email.'})

@app.route('/api/reset_password', methods=['POST'])
def reset_password():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    otp = data.get('otp', '').strip()
    new_password = data.get('new_password', '')
    if not (email and otp and new_password):
        return jsonify({'error': 'All fields required'}), 400
    record = reset_otps.get(email)
    if not record or record['otp'] != otp:
        return jsonify({'error': 'Invalid OTP'}), 400
    if datetime.datetime.utcnow() > record['expires']:
        return jsonify({'error': 'OTP expired'}), 400
    hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    users.update_one({'email': email}, {'$set': {'password': hashed}})
    reset_otps.pop(email, None)
    return jsonify({'success': True, 'message': 'Password reset successful.'})

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

@app.route('/download_report', methods=['GET'])
@token_required
def download_report(current_user):
    # Fetch user data from MongoDB
    user = users.find_one({'email': current_user['email']})
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Prepare PDF in memory
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 50

    p.setFont('Helvetica-Bold', 20)
    p.drawString(50, y, 'FitFusion User Report')
    y -= 40
    p.setFont('Helvetica', 14)
    p.drawString(50, y, f"Name: {user.get('name', '')}")
    y -= 30
    p.drawString(50, y, f"Email: {user.get('email', '')}")
    y -= 30
    p.drawString(50, y, f"Age: {user.get('age', '')}")
    y -= 30
    p.drawString(50, y, f"Gender: {user.get('gender', '')}")
    y -= 30
    p.drawString(50, y, f"Height: {user.get('height', '')} cm")
    y -= 30
    p.drawString(50, y, f"Weight: {user.get('weight', '')} kg")
    y -= 30
    p.drawString(50, y, f"Fitness Goal: {user.get('fitness_goal', '')}")
    y -= 30
    # Add more attributes as needed

    p.showPage()
    p.save()
    buffer.seek(0)

    response = make_response(buffer.read())
    response.headers.set('Content-Type', 'application/pdf')
    response.headers.set('Content-Disposition', 'attachment', filename='FitFusion_User_Report.pdf')
    return response

if __name__ == "__main__":
    app.run(debug=True)

print(app.url_map)
