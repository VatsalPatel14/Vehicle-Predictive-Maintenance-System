from flask import Flask, render_template, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import os
import mysql.connector
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

if not app.secret_key:
    raise RuntimeError("Please set the FLASK_SECRET_KEY environment variable.")

# ---------------- DB ----------------

def get_db():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "vehicle_app")
    )


# ---------------- MODEL ----------------
import joblib

model = joblib.load("vehicle_model.pkl")

# ---------------- AUTH ----------------
@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"].strip()

        if not name or not email or not password:
            return "❌ All fields required"

        conn = get_db()
        cur = conn.cursor()

        # check existing email
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        if cur.fetchone():
            conn.close()
            return "⚠️ Email already exists"

        # insert user
        hashed_password = generate_password_hash(password)
        cur.execute(
            "INSERT INTO users (name,email,password) VALUES (%s,%s,%s)",
            (name, email, hashed_password)
        )
        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"].strip()

        conn = get_db()
        cur = conn.cursor()

        try:
            cur.execute(
                "SELECT * FROM users WHERE email=%s",
                (email,)
            )
            user = cur.fetchone()

            if not user:
                return "User not found", 401

            stored_password = user[3]

            if stored_password.startswith(("scrypt:", "pbkdf2:")):
                password_ok = check_password_hash(
                    stored_password, password
                )
            else:
                # Temporary support for existing plain-text passwords
                password_ok = (stored_password == password)

                if password_ok:
                    hashed_password = generate_password_hash(password)
                    cur.execute(
                        "UPDATE users SET password=%s WHERE id=%s",
                        (hashed_password, user[0])
                    )
                    conn.commit()

            if password_ok:
                session["user_id"] = user[0]
                session["name"] = user[1]
                return redirect("/")

            return "Wrong password", 401

        finally:
            cur.close()
            conn.close()

    return render_template("login.html")



@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- ROUTES ----------------

# @app.route("/")
# def dashboard():
#     if "user_id" not in session:
#         return redirect("/login")

#     conn = get_db()
#     cur = conn.cursor()

#     # total vehicles
#     cur.execute("SELECT COUNT(*) FROM vehicles WHERE user_id=%s", (session["user_id"],))
#     total_vehicles = cur.fetchone()[0]

#     # total predictions
#     cur.execute("SELECT COUNT(*) FROM history WHERE user_id=%s", (session["user_id"],))
#     total_predictions = cur.fetchone()[0]

#     # maintenance required count
#     cur.execute("SELECT COUNT(*) FROM history WHERE user_id=%s AND result LIKE '%Maintenance%'", (session["user_id"],))
#     maintenance_due = cur.fetchone()[0]


#     cur.execute("""
#         SELECT v.name, h.result, h.created_at
#         FROM history h
#         JOIN vehicles v ON h.vehicle_id = v.id
#         WHERE v.user_id = %s
#         ORDER BY h.created_at DESC
#         LIMIT 5
#     """, (session["user_id"],))
#     recent_alerts = cur.fetchall()


#     conn.close()

#     return render_template(
#         "dashboard.html",
#         name=session["name"],
#         total_vehicles=total_vehicles,
#         total_predictions=total_predictions,
#         maintenance_due=maintenance_due
#         recent_alerts=recent_alerts
#     )

@app.route("/")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM vehicles WHERE user_id=%s", (session["user_id"],))
    total_vehicles = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM history WHERE user_id=%s", (session["user_id"],))
    total_predictions = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM history WHERE user_id=%s AND result LIKE '%Maintenance%'", (session["user_id"],))
    maintenance_due = cur.fetchone()[0]

    # ✅ ADD THIS — feeds the Recent Alerts table
    cur.execute("""
        SELECT v.name, h.result, h.created_at
        FROM history h
        JOIN vehicles v ON h.vehicle_id = v.id
        WHERE v.user_id = %s
        ORDER BY h.created_at DESC
        LIMIT 5
    """, (session["user_id"],))
    recent_alerts = cur.fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        name=session["name"],
        total_vehicles=total_vehicles,
        total_predictions=total_predictions,
        maintenance_due=maintenance_due,
        recent_alerts=recent_alerts   # ✅ ADD THIS
    )


# VEHICLES
@app.route("/vehicles", methods=["GET","POST"])
def vehicles():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        name = request.form["name"]
        mileage = request.form["mileage"]

        cur.execute(
            "INSERT INTO vehicles (name,mileage,user_id) VALUES (%s,%s,%s)",
            (name, mileage, session["user_id"])
        )
        conn.commit()

    cur.execute("SELECT * FROM vehicles WHERE user_id=%s", (session["user_id"],))
    data = cur.fetchall()

    conn.close()

    return render_template("vehicles.html", vehicles=data)


@app.route("/delete_vehicle/<int:id>")
def delete_vehicle(id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    # 🔐 DELETE only user's vehicle
    cur.execute(
        "DELETE FROM vehicles WHERE id=%s AND user_id=%s",
        (id, session["user_id"])
    )

    conn.commit()
    conn.close()

    return redirect("/vehicles")

# @app.route("/prediction")
# def prediction_page():
#     return render_template("prediction.html")
@app.route("/prediction")
def prediction_page():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    # 📦 Fetch user vehicles
    cur.execute("SELECT id, name FROM vehicles WHERE user_id=%s", (session["user_id"],))
    vehicles = cur.fetchall()

    conn.close()

    return render_template("prediction.html", vehicles=vehicles)

# PREDICTION

@app.route("/predict", methods=["POST"])
def predict():

    if "user_id" not in session:
        return redirect("/login")

    vehicle_id = request.form["vehicle_id"]

    # GET DATA
    mileage = float(request.form["Mileage"])
    odometer = float(request.form["Odometer_Reading"])
    issues = int(request.form["Reported_Issues"])
    age = int(request.form["Vehicle_Age"])

    service = int(request.form["Service_History"])
    tire = int(request.form["Tire_Condition"])
    brake = int(request.form["Brake_Condition"])
    battery = int(request.form["Battery_Status"])

    owner = {"First":0,"Second":1,"Third":2}.get(request.form["Owner_Type"],0)
    history = {"Poor":0,"Average":1,"Good":2}.get(request.form["Maintenance_History"],1)

    data = [[
        mileage, odometer, issues, age,
        service, tire, brake, battery,
        owner, history
    ]]

    # PREDICT
    pred = model.predict(data)[0]
    prob = model.predict_proba(data)[0].max()

    health_score = round((1 - prob) * 100, 2) if pred == 1 else round(prob * 100, 2)

    result = "⚠️ Maintenance Required" if pred == 1 else "✅ Healthy"
    confidence = round(prob * 100, 2)

    conn = get_db()
    cur = conn.cursor()

    # fetch vehicles again
    cur.execute("SELECT id, name FROM vehicles WHERE user_id=%s", (session["user_id"],))
    vehicles = cur.fetchall()

    # save history
    cur.execute(
        "INSERT INTO history (vehicle_id, result, confidence, user_id) VALUES (%s,%s,%s,%s)",
        (vehicle_id, result, confidence, session["user_id"])
    )

    conn.commit()
    conn.close()

    return render_template(
        "prediction.html",
        prediction=result,
        confidence=confidence,
        health_score=health_score,
        vehicles=vehicles
    )

# HISTORY
@app.route("/history")
def history():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT v.name, h.result, h.confidence, h.created_at
    FROM history h
    JOIN vehicles v ON h.vehicle_id = v.id
    WHERE v.user_id = %s
    """, (session['user_id'],))
    data = cur.fetchall()

    conn.close()
    return render_template("history.html", history=data)

# PROFILE
@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    # get user data
    cur.execute(
        "SELECT name, email FROM users WHERE id=%s",
        (session["user_id"],)
    )
    user = cur.fetchone()

    # total vehicles
    cur.execute(
        "SELECT COUNT(*) FROM vehicles WHERE user_id=%s",
        (session["user_id"],)
    )
    total_vehicles = cur.fetchone()[0]

    # total predictions
    cur.execute(
        "SELECT COUNT(*) FROM history WHERE user_id=%s",
        (session["user_id"],)
    )
    total_predictions = cur.fetchone()[0]

    conn.close()

    return render_template(
        "profile.html",
        user=user,
        total_vehicles=total_vehicles,
        total_predictions=total_predictions
    )
# ---------------- EDIT PROFILE ----------------
@app.route("/edit_profile", methods=["POST"])
def edit_profile():
    if "user_id" not in session:
        return redirect("/login")

    name = request.form["name"]
    email = request.form["email"]

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "UPDATE users SET name=%s, email=%s WHERE id=%s",
        (name, email, session["user_id"])
    )

    conn.commit()
    conn.close()

    session["name"] = name

    flash("✅ Profile updated successfully!", "success")
    return redirect("/profile")


# ---------------- CHANGE PASSWORD ----------------

@app.route("/change_password", methods=["POST"])
def change_password():
    if "user_id" not in session:
        return redirect("/login")

    old_password = request.form["old_password"]
    new_password = request.form["new_password"]

    if not new_password.strip():
        flash("New password cannot be empty.", "error")
        return redirect("/profile")

    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute(
            "SELECT password FROM users WHERE id=%s",
            (session["user_id"],)
        )
        user = cur.fetchone()

        if not user:
            flash("User not found.", "error")
            return redirect("/profile")

        stored_password = user[0]

        if stored_password.startswith(("scrypt:", "pbkdf2:")):
            password_ok = check_password_hash(stored_password, old_password)
        else:
            # Support an existing plain-text password during migration
            password_ok = (stored_password == old_password)

        if password_ok:
            hashed_password = generate_password_hash(new_password)

            cur.execute(
                "UPDATE users SET password=%s WHERE id=%s",
                (hashed_password, session["user_id"])
            )
            conn.commit()
            flash("Password changed successfully!", "success")
        else:
            flash("Wrong old password!", "error")

    finally:
        cur.close()
        conn.close()

    return redirect("/profile")




# ---------------- GRAPH ----------------

@app.route("/charts")
def charts():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT result, COUNT(*)
        FROM history
        WHERE user_id=%s
        GROUP BY result
    """, (session["user_id"],))

    data = cur.fetchall()


    labels = [d[0] for d in data]
    values = [d[1] for d in data]

    # 🎨 Use seaborn style
    sns.set_style("whitegrid")

    # 📊 Create bar plot
    plt.figure(figsize=(6,4))

    colors = ["#6366f1", "#06b6d4"]  # purple + cyan

    bars = plt.bar(labels, values, color=colors)

    # Add glow effect
    for bar in bars:
        bar.set_edgecolor("black")
        bar.set_linewidth(0.5)

    plt.title("Prediction Analysis", fontsize=14, fontweight="bold")
    plt.xlabel("Result")
    plt.ylabel("Count")

    plt.grid(axis='y', linestyle='--', alpha=0.3)

    plt.tight_layout()

    # Convert plot to image
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)

    graph1 = base64.b64encode(img.getvalue()).decode()

    plt.close()


#----------------graph-2--------------------#
    plt.figure(figsize=(6,4))

    colors = ["#ef4444","#22c55e", ]  # green + red

    plt.pie(
        values,
        labels=labels,
        autopct='%1.1f%%',
        startangle=90,
        colors=colors,
        wedgeprops={'linewidth': 2, 'edgecolor': 'white'}
    )

    # Donut style
    centre_circle = plt.Circle((0,0),0.65,fc='white')
    plt.gca().add_artist(centre_circle)

    plt.title("Prediction Distribution", fontsize=14, fontweight="bold")

    plt.tight_layout()
    img2 = io.BytesIO()
    plt.savefig(img2, format='png')
    img2.seek(0)
    graph2 = base64.b64encode(img2.getvalue()).decode()
    plt.close()
    conn.close()
    return render_template("charts.html", graph1=graph1, graph2=graph2)



if __name__ == "__main__":
    app.run(debug=True)
