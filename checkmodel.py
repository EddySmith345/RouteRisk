import joblib

model = joblib.load("models/delivery_time_model.pkl")

print("Model type:")
print(type(model))

print("\nModel details:")
print(model)

if hasattr(model, "named_steps"):
    print("\nPipeline steps:")
    for name, step in model.named_steps.items():
        print(f"- {name}: {type(step)}")