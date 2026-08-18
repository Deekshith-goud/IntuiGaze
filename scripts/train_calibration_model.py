import csv
import glob
import os
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error


def main() -> None:
    print("--- EyeNav Pure ML Calibration Training ---")
    search_path = os.path.join("data", "calibration_*.csv")
    files = glob.glob(search_path)

    if len(files) == 0:
        print("ERROR: No calibration datasets found! Run 'scripts/calibrate_ml.py' first.")
        return

    print(f"Found {len(files)} pure calibration datasets.")

    X_all = []
    y_all = []

    for f in files:
        with open(f) as file:
            reader = csv.DictReader(file)
            for row in reader:
                features = [
                    float(row['gaze_x']),
                    float(row['gaze_y']),
                    float(row['head_pitch']),
                    float(row['head_yaw']),
                    float(row['head_roll'])
                ]
                labels = [float(row['target_x']), float(row['target_y'])]
                X_all.append(features)
                y_all.append(labels)

    X_all = np.array(X_all)
    y_all = np.array(y_all)

    print(f"Extracted {len(X_all)} pure ground-truth coordinates.")

    # We use all data for training since calibration data is pure and scarce
    print("Training Random Forest Regressor...")
    model = RandomForestRegressor(n_estimators=150, max_depth=20, random_state=42, n_jobs=-1)
    model.fit(X_all, y_all)

    # Evaluate on the training set just to verify it learned the spatial mapping
    predictions = model.predict(X_all)
    mae = mean_absolute_error(y_all, predictions)
    print(f"Training Complete! Mean Absolute Error (MAE): {mae:.2f} pixels.")

    # Save Model
    model_dir = Path("backend/eyenav/models")
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / "spatial_mapper.pkl"

    joblib.dump(model, model_path)
    print(f"Model successfully saved to {model_path}")

if __name__ == "__main__":
    main()
