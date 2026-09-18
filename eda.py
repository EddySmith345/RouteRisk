import pandas as pd
import matplotlib.pyplot as plt

# Load dataset
df = pd.read_csv("data/Food_Delivery_Times.csv")


# 1. Distance vs Delivery Time
plt.figure(figsize=(8, 5))
plt.scatter(df["Distance_km"], df["Delivery_Time_min"])
plt.xlabel("Distance (km)")
plt.ylabel("Delivery Time (minutes)")
plt.title("Distance vs Delivery Time")
plt.show()


# 2. Weather vs Delivery Time
plt.figure(figsize=(8, 5))
df.boxplot(column="Delivery_Time_min", by="Weather")
plt.xlabel("Weather")
plt.ylabel("Delivery Time (minutes)")
plt.title("Weather vs Delivery Time")
plt.suptitle("")
plt.show()


# 3. Traffic vs Delivery Time
plt.figure(figsize=(8, 5))
df.boxplot(column="Delivery_Time_min", by="Traffic_Level")
plt.xlabel("Traffic Level")
plt.ylabel("Delivery Time (minutes)")
plt.title("Traffic vs Delivery Time")
plt.suptitle("")
plt.show()


# 4. Time of Day vs Delivery Time
plt.figure(figsize=(8, 5))
df.boxplot(column="Delivery_Time_min", by="Time_of_Day")
plt.xlabel("Time of Day")
plt.ylabel("Delivery Time (minutes)")
plt.title("Time of Day vs Delivery Time")
plt.suptitle("")
plt.show()