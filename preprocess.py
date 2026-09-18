import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder


# Load dataset
df = pd.read_csv("data/Food_Delivery_Times.csv")

# Remove ID
df = df.drop(columns=["Order_ID"])


# Separate features and target
X = df.drop(columns=["Delivery_Time_min"])
y = df["Delivery_Time_min"]


# Numerical features
numerical_features = [
    "Distance_km",
    "Preparation_Time_min",
    "Courier_Experience_yrs"
]


# Categorical features
categorical_features = [
    "Weather",
    "Traffic_Level",
    "Time_of_Day",
    "Vehicle_Type"
]

# Preprocessing helped in by ChatGPT
# Numerical preprocessing
numerical_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median"))
])


# Categorical preprocessing
categorical_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("encoder", OneHotEncoder(handle_unknown="ignore"))
])


# Combine preprocessing
preprocessor = ColumnTransformer([
    ("numerical", numerical_pipeline, numerical_features),
    ("categorical", categorical_pipeline, categorical_features)
])


# Transform the data
X_processed = preprocessor.fit_transform(X)


print("Original feature shape:")
print(X.shape)

print("\nProcessed feature shape:")
print(X_processed.shape)

print("\nPreprocessing complete!")