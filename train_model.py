import pandas as pd
import matplotlib.pyplot as plt
import joblib
import numpy as np

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score



# =========================
# 1. LOAD DATA
# =========================

df = pd.read_csv("data/Food_Delivery_Times.csv")


# Remove Order ID
df = df.drop(columns=["Order_ID"])


# =========================
# 2. SEPARATE FEATURES/TARGET
# =========================

X = df.drop(columns=["Delivery_Time_min"])
y = df["Delivery_Time_min"]


# =========================
# 3. DEFINE FEATURES
# =========================

numerical_features = [
    "Distance_km",
    "Preparation_Time_min",
    "Courier_Experience_yrs"
]

categorical_features = [
    "Weather",
    "Traffic_Level",
    "Time_of_Day",
    "Vehicle_Type"
]


# =========================
# 4. PREPROCESSING
# =========================

numerical_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median"))
])

categorical_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("encoder", OneHotEncoder(handle_unknown="ignore"))
])


preprocessor = ColumnTransformer([
    ("numerical", numerical_pipeline, numerical_features),
    ("categorical", categorical_pipeline, categorical_features)
])


# =========================
# 5. 80% TRAIN 20% TEST
# =========================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)


print("Training samples:", len(X_train))
print("Testing samples:", len(X_test))


# =========================
# 6. CREATE MODEL
# =========================

#Linear Regression tested better than Random Forest and Gradient Boosting
model = Pipeline([
    ("preprocessor", preprocessor),
    ("regressor", LinearRegression())
])


# =========================
# 7. TRAIN MODEL
# =========================

model.fit(X_train, y_train)

# Save the trained model
joblib.dump(model, "models/delivery_time_model.pkl")

print("Model saved successfully!")


# =========================
# 8. MAKE PREDICTIONS
# =========================

predictions = model.predict(X_test)

# Calculate prediction errors
errors = y_test - predictions
absolute_errors = np.abs(errors)

# Calculate error statistics
mean_error = np.mean(errors)
mae_error = np.mean(absolute_errors)

# Prediction error percentiles
p50 = np.percentile(absolute_errors, 50)
p80 = np.percentile(absolute_errors, 80)
p95 = np.percentile(absolute_errors, 95)

print("\n===== PREDICTION ERROR ANALYSIS =====")
print(f"Mean Error:       {mean_error:.2f} minutes")
print(f"Mean Abs Error:   {mae_error:.2f} minutes")
print(f"50th percentile:  {p50:.2f} minutes")
print(f"80th percentile:  {p80:.2f} minutes")
print(f"95th percentile:  {p95:.2f} minutes")


# =========================
# 9. EVALUATE MODEL
# =========================

mae = mean_absolute_error(y_test, predictions)
rmse = mean_squared_error(y_test, predictions) ** 0.5
r2 = r2_score(y_test, predictions)


print("\n===== MODEL RESULTS =====")

print(f"MAE:  {mae:.2f} minutes")
print(f"RMSE: {rmse:.2f} minutes")
print(f"R²:   {r2:.3f}")
# Actual vs Predicted plot
plt.figure(figsize=(8, 6))

plt.scatter(y_test, predictions)

# Perfect prediction line
plt.plot(
    [y_test.min(), y_test.max()],
    [y_test.min(), y_test.max()]
)

plt.xlabel("Actual Delivery Time (minutes)")
plt.ylabel("Predicted Delivery Time (minutes)")
plt.title("Actual vs Predicted Delivery Time")

plt.show()