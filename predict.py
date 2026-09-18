import joblib
import pandas as pd


# ============================================================
# 1. LOAD TRAINED MODEL
# ============================================================

model = joblib.load("models/delivery_time_model.pkl")


# ============================================================
# 2. PREDICT DELIVERY TIME
# ============================================================

def predict_delivery(
    distance,
    weather,
    traffic,
    time_of_day,
    vehicle,
    preparation_time,
    experience
):
    # Create input DataFrame
    delivery = pd.DataFrame([{
        "Distance_km": distance,
        "Weather": weather,
        "Traffic_Level": traffic,
        "Time_of_Day": time_of_day,
        "Vehicle_Type": vehicle,
        "Preparation_Time_min": preparation_time,
        "Courier_Experience_yrs": experience
    }])

    # Make prediction
    prediction = model.predict(delivery)[0]

    # Model uncertainty from test-set analysis
    error_margin = 16.40

    # Calculate expected range
    lower = max(0, prediction - error_margin)
    upper = prediction + error_margin

    return prediction, lower, upper


# ============================================================
# 3. CALCULATE DELIVERY RISK
# ============================================================

def calculate_risk(
    distance,
    weather,
    traffic,
    time_of_day,
    experience
):
    score = 0
    reasons = []

    # -------------------------
    # Traffic
    # -------------------------

    if traffic == "High":
        score += 35
        reasons.append("High traffic")

    elif traffic == "Medium":
        score += 15
        reasons.append("Moderate traffic")


    # -------------------------
    # Weather
    # -------------------------

    if weather == "Snowy":
        score += 30
        reasons.append("Snowy weather")

    elif weather == "Rainy":
        score += 20
        reasons.append("Rainy weather")

    elif weather == "Foggy":
        score += 15
        reasons.append("Foggy weather")

    elif weather == "Windy":
        score += 10
        reasons.append("Windy weather")


    # -------------------------
    # Time of Day
    # -------------------------

    if time_of_day == "Evening":
        score += 10
        reasons.append("Evening delivery")


    # -------------------------
    # Distance
    # -------------------------

    if distance >= 15:
        score += 10
        reasons.append("Long delivery distance")


    # -------------------------
    # Courier Experience
    # -------------------------

    if experience < 2:
        score += 10
        reasons.append("Limited courier experience")


    # -------------------------
    # Determine Risk Level
    # -------------------------

    if score >= 60:
        risk = "HIGH"

    elif score >= 30:
        risk = "MEDIUM"

    else:
        risk = "LOW"

    return score, risk, reasons


# ============================================================
# 4. TEST ROUTERISK
# ============================================================

prediction, lower, upper = predict_delivery(
    distance=12.0,
    weather="Rainy",
    traffic="High",
    time_of_day="Evening",
    vehicle="Bike",
    preparation_time=20,
    experience=2.0
)


score, risk, reasons = calculate_risk(
    distance=12.0,
    weather="Rainy",
    traffic="High",
    time_of_day="Evening",
    experience=2.0
)


# ============================================================
# 5. DISPLAY RESULTS
# ============================================================

print("========================================")
print("          ROUTERISK PREDICTION")
print("========================================")

print(f"\nPredicted delivery time: {prediction:.1f} minutes")

print(
    f"Expected range: "
    f"{lower:.1f} - {upper:.1f} minutes"
)

print(f"\nRisk Score: {score}/100")
print(f"Risk Level: {risk}")

print("\nRisk Factors:")

for reason in reasons:
    print(f"- {reason}")

print("========================================")