import pandas as pd
import matplotlib.pyplot as plt

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LinearRegression


# =========================
# LOAD DATA
# =========================

df = pd.read_csv("data/Food_Delivery_Times.csv")


# =========================
# FEATURES AND TARGET
# =========================

X = df.drop(columns=["Order_ID", "Delivery_Time_min"])
y = df["Delivery_Time_min"]


# =========================
# FEATURE TYPES
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
# PREPROCESSING
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
# MODEL
# =========================

model = Pipeline([
    ("preprocessor", preprocessor),
    ("regressor", LinearRegression())
])


# =========================
# TRAIN MODEL
# =========================

model.fit(X, y)


# =========================
# GET FEATURE NAMES
# =========================

feature_names = model.named_steps[
    "preprocessor"
].get_feature_names_out()


# =========================
# GET COEFFICIENTS
# =========================

coefficients = model.named_steps[
    "regressor"
].coef_


# =========================
# CREATE FEATURE TABLE
# =========================

importance = pd.DataFrame({
    "Feature": feature_names,
    "Coefficient": coefficients
})

importance["Absolute_Impact"] = importance["Coefficient"].abs()

importance = importance.sort_values(
    "Absolute_Impact",
    ascending=False
)


# =========================
# PRINT RESULTS
# =========================

print("\n===== FEATURE COEFFICIENTS =====")

print(
    importance[
        ["Feature", "Coefficient"]
    ].to_string(index=False)
)


print("\n===== TOP 10 MOST INFLUENTIAL FEATURES =====")

print(
    importance[
        ["Feature", "Coefficient"]
    ].head(10).to_string(index=False)
)


# =========================
# PLOT
# =========================

top_features = importance.head(10).sort_values(
    "Coefficient"
)

plt.figure(figsize=(10, 6))

plt.barh(
    top_features["Feature"],
    top_features["Coefficient"]
)

plt.xlabel("Regression Coefficient")
plt.ylabel("Feature")
plt.title("Top 10 Features Influencing Delivery Time")

plt.tight_layout()
plt.show()