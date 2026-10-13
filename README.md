# Vehicle Predictive Maintenance System Using Machine Learning

A machine learning web application that predicts whether a vehicle requires maintenance based on vehicle condition, usage, and maintenance history.

## Project Overview

The Vehicle Predictive Maintenance System is designed to help users assess vehicle maintenance needs using a trained machine learning model. The application provides user authentication, vehicle management, maintenance predictions, prediction history, and a dashboard.

This project was developed as an academic machine learning project.

## Features

- User registration and login
- Vehicle information management
- Machine learning-based maintenance prediction
- Prediction confidence display
- Prediction history
- User profile management
- Password change functionality
- Dashboard with vehicle and prediction summaries
- Prediction analysis charts

## Technologies Used

- **Language:** Python
- **Web Framework:** Flask
- **Machine Learning:** Scikit-learn, Random Forest
- **Data Processing:** Pandas, NumPy
- **Visualization:** Matplotlib, Seaborn
- **Database:** MySQL
- **Frontend:** HTML, CSS, JavaScript
- **Model Storage:** Joblib

## Model Input Features

- Mileage
- Odometer Reading
- Reported Issues
- Vehicle Age
- Service History
- Tire Condition
- Brake Condition
- Battery Status
- Owner Type
- Maintenance History

The trained model returns a prediction indicating whether maintenance is required.

## Project Structure

- `app.py` â€” Flask application and routes
- `vehicle_model.pkl` â€” Trained machine learning model
- `dataset.csv` â€” Dataset used by the project
- `templates/` â€” HTML templates
- `requirements.txt` â€” Python dependencies
- `.gitignore` â€” Files excluded from Git

## Prerequisites

- Python 3.11 or a compatible Python version
- MySQL Server
- Git

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/VatsalPatel14/Vehicle-Predictive-Maintenance-System.git
cd Vehicle-Predictive-Maintenance-System
```

### 2. Create and activate a virtual environment

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Configure the database

Create and configure the MySQL database and tables required by the application. Update the database connection settings to match your local MySQL configuration.

### 5. Set the Flask secret key

In PowerShell, generate a secret key for the current terminal session:

```powershell
$env:FLASK_SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"
```

Do not publish your secret key or database credentials.

### 6. Run the application

```powershell
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

## Disclaimer

This project is intended for educational purposes. Model predictions are estimates and should not replace professional vehicle inspections or maintenance advice.

## Author

**Vatsal Patel**
