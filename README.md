# RouteRisk

#### Video Demo: 

#### Description:
RouteRisk is a desktop application that predicts last-mile delivery times using machine learning and provides an additional delivery risk assessment based on factors such as traffic, weather, distance, time of day, and courier experience.

The application is designed to help estimate how long a delivery may take while also highlighting factors that could contribute to delivery delays.

---

## Features

### Delivery Time Prediction

RouteRisk uses a trained machine learning model to estimate delivery time based on:

- Delivery distance
- Weather conditions
- Traffic level
- Time of day
- Vehicle type
- Order preparation time (Decided by type of item ordered)
- Courier experience

The application displays:

- Predicted delivery time
- Expected prediction range
- Visual representation of the prediction range

---

### Delivery Risk Assessment

In addition to the machine learning prediction, RouteRisk calculates a separate risk score.

The risk calculation considers:

- Traffic conditions
- Weather conditions
- Time of day
- Delivery distance
- Courier experience

The application categorizes the result as:

- **LOW**
- **MEDIUM**
- **HIGH**

It also displays the factors contributing to the risk score.

---

## Item Selection System

RouteRisk includes a searchable database of delivery items.

Users can:

- Search for items using an autocomplete search bar
- Select multiple items
- Remove individual items
- View their selected items
- Automatically calculate the preparation time based on the selected items

The preparation time is based on the item requiring the longest preparation time.

This helps prevent unrealistic preparation-time inputs and allows the application to simulate more realistic delivery orders.

The item database contains thousands of products across multiple categories, including:

- Food
- Beverages
- Packaged goods
- Electronics
- Toys
- Clothing
- Home and kitchen
- Sports equipment
- Pet supplies
- Baby products
- Books and stationery
- Automotive products
- Hardware and DIY
- Garden and outdoor products
- Travel products
- Crafts and hobbies
- And more

---

## Machine Learning Model

The prediction component uses a supervised machine learning regression model trained on delivery-time data.

The model uses delivery-related features to learn the relationship between delivery conditions and the time required to complete a delivery.

The trained model is saved as:

`models/delivery_time_model.pkl`

The application loads this trained model when making predictions.

---

## Dataset

The project uses a delivery-time dataset containing information related to delivery conditions and delivery duration.

The main dataset is stored in:

`data/Food_Delivery_Times.csv`

The project also contains a separate item database:

`data/items_database.csv`

The item database is used by the application's order and preparation-time system.

---

## Risk Calculation

The risk score is calculated separately from the machine learning prediction.

Example risk contributions include:

| Factor | Condition | Score |
|---|---|---:|
| Traffic | High | +35 |
| Traffic | Medium | +15 |
| Weather | Snowy | +30 |
| Weather | Rainy | +20 |
| Weather | Foggy | +15 |
| Weather | Windy | +10 |
| Time | Evening | +10 |
| Distance | 15 km or more | +10 |
| Experience | Less than 2 years | +10 |

The final score determines the displayed risk level.

### Risk Levels

- **0–29:** LOW
- **30–59:** MEDIUM
- **60+:** HIGH

The risk score is intended as an additional indicator and is separate from the machine learning prediction.

---

## Training Range

The application allows users to enter values outside the range represented in the training data.

When this happens, RouteRisk displays a warning indicating that the prediction may be less reliable outside the training range.

This allows the application to demonstrate how machine learning predictions can become less reliable when given inputs substantially different from the data used to train the model.

---

## Technology Used

RouteRisk was developed using:

- **Python**
- **PySide6** — desktop graphical user interface
- **Pandas** — data processing
- **Scikit-learn** — machine learning
- **Joblib** — saving and loading the trained model
- **CSV** — item and delivery datasets

---
