"""IntuiGaze — Regression Model Evaluation Script.
==============================================

Evaluates empirical spatial mapping models on ground-truth calibration data
collected from `scripts/calibrate_ml.py` and stored in `data/`.

Evaluates:
  1. Level 0: Screen Center Dummy Baseline (fixed central gaze)
  2. Level 1: Direct 2D Gaze Heuristic
  3. Level 2: Supervised Random Forest Regressor (`spatial_mapper.pkl`)
  4. Level 3: Degree-2 Polynomial Ridge Regression (5-fold Cross-Validation)

Metrics computed per model:
  - MAE X, MAE Y, and Total Mean Absolute Error (pixels)
  - RMSE (pixels)
  - Euclidean Error Distribution: Mean, Median (P50), P90, P95, Max (pixels)
  - UI Target Hit Rates: Hit@25px, Hit@50px, Hit@75px, Hit@100px (%)
  - Visual Angular Error in degrees (assumes 1080p, 60cm viewing distance)
"""

from __future__ import annotations

import argparse
import glob
import math
import os
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import KFold

# Screen geometry parameters (1080p reference)
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
VIEWING_DISTANCE_CM = 60.0
PIXEL_PITCH_CM = 0.02767  # 24" 1080p monitor (53.13cm width / 1920px)


def pixel_to_visual_degrees(pixel_dist: float) -> float:
    """Convert on-screen pixel displacement to visual angle error in degrees."""
    dist_cm = pixel_dist * PIXEL_PITCH_CM
    rad = math.atan2(dist_cm, VIEWING_DISTANCE_CM)
    return math.degrees(rad)


def evaluate_predictions(y_true: np.ndarray, y_pred: np.ndarray, model_name: str) -> dict:
    """Compute comprehensive regression metrics comparing y_pred to y_true."""
    mae_x = float(mean_absolute_error(y_true[:, 0], y_pred[:, 0]))
    mae_y = float(mean_absolute_error(y_true[:, 1], y_pred[:, 1]))
    rmse_x = float(np.sqrt(mean_squared_error(y_true[:, 0], y_pred[:, 0])))
    rmse_y = float(np.sqrt(mean_squared_error(y_true[:, 1], y_pred[:, 1])))

    # Euclidean distance per point
    euc_errors = np.sqrt(np.sum((y_pred - y_true) ** 2, axis=1))

    mean_euc = float(np.mean(euc_errors))
    median_euc = float(np.median(euc_errors))
    p90_euc = float(np.percentile(euc_errors, 90))
    p95_euc = float(np.percentile(euc_errors, 95))
    max_euc = float(np.max(euc_errors))

    # Hit rates at UI widget tolerances
    hit_25 = float(np.mean(euc_errors <= 25.0) * 100.0)
    hit_50 = float(np.mean(euc_errors <= 50.0) * 100.0)
    hit_75 = float(np.mean(euc_errors <= 75.0) * 100.0)
    hit_100 = float(np.mean(euc_errors <= 100.0) * 100.0)

    # Angular error in degrees
    angular_median_deg = pixel_to_visual_degrees(median_euc)
    angular_mean_deg = pixel_to_visual_degrees(mean_euc)

    return {
        "model": model_name,
        "n_samples": len(y_true),
        "mae_x": mae_x,
        "mae_y": mae_y,
        "mae_combined": (mae_x + mae_y) / 2.0,
        "rmse_x": rmse_x,
        "rmse_y": rmse_y,
        "mean_euclidean": mean_euc,
        "median_euclidean": median_euc,
        "p90_euclidean": p90_euc,
        "p95_euclidean": p95_euc,
        "max_euclidean": max_euc,
        "hit_25px": hit_25,
        "hit_50px": hit_50,
        "hit_75px": hit_75,
        "hit_100px": hit_100,
        "angular_median_deg": angular_median_deg,
        "angular_mean_deg": angular_mean_deg,
    }


def find_calibration_datasets(data_dir: str = "data") -> list[str]:
    """Find all calibration CSV files in data/ and subfolders."""
    patterns = [
        os.path.join(data_dir, "calibration_*.csv"),
        os.path.join(data_dir, "**", "calibration_*.csv"),
    ]
    files: list[str] = []
    for pat in patterns:
        files.extend(glob.glob(pat, recursive=True))
    return sorted(list(set(files)))


def fit_and_eval_polynomial_cv(X: np.ndarray, y: np.ndarray, n_splits: int = 5) -> np.ndarray:
    """Evaluate Degree-2 Polynomial Ridge Regression using K-Fold Cross Validation."""
    kf = KFold(n_splits=min(n_splits, len(X)), shuffle=True, random_state=42)
    y_pred_cv = np.zeros_like(y)

    # Feature expansion: [1, x1, x2, ..., x1^2, x1*x2, ...]
    def poly_expand(mat: np.ndarray) -> np.ndarray:
        n, d = mat.shape
        terms = [np.ones((n, 1))]
        for i in range(d):
            terms.append(mat[:, i : i + 1])
        for i in range(d):
            for j in range(i, d):
                terms.append((mat[:, i] * mat[:, j])[:, np.newaxis])
        return np.hstack(terms)

    Phi = poly_expand(X)
    lambda_reg = 1e-4

    for train_idx, val_idx in kf.split(Phi):
        Phi_tr, Phi_val = Phi[train_idx], Phi[val_idx]
        y_tr = y[train_idx]

        ridge = lambda_reg * np.eye(Phi_tr.shape[1])
        XtX = Phi_tr.T @ Phi_tr + ridge
        coeff_x = np.linalg.solve(XtX, Phi_tr.T @ y_tr[:, 0])
        coeff_y = np.linalg.solve(XtX, Phi_tr.T @ y_tr[:, 1])

        y_pred_cv[val_idx, 0] = Phi_val @ coeff_x
        y_pred_cv[val_idx, 1] = Phi_val @ coeff_y

    return y_pred_cv


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate IntuiGaze spatial regression models")
    parser.add_argument("--data-dir", default="data", help="Directory containing calibration datasets")
    parser.add_argument("--model-path", default="backend/eyenav/models/spatial_mapper.pkl", help="Path to Random Forest model")
    args = parser.parse_args()

    print("=" * 80)
    print("      IntuiGaze — Ground-Truth Spatial Model Evaluation")
    print("=" * 80)

    calib_files = find_calibration_datasets(args.data_dir)
    if not calib_files:
        print(f"Error: No calibration CSV files found in '{args.data_dir}'.")
        print("Run 'scripts/calibrate_ml.py' to generate ground-truth calibration data.")
        sys.exit(1)

    print(f"Found {len(calib_files)} calibration dataset(s):")
    for f in calib_files:
        print(f"  • {f}")

    # Load and concatenate all calibration data
    dfs = [pd.read_csv(f) for f in calib_files]
    df = pd.concat(dfs, ignore_index=True)
    print(f"Loaded {len(df)} total ground-truth calibration points.\n")

    feature_cols = ["gaze_x", "gaze_y", "head_pitch", "head_yaw", "head_roll"]
    target_cols = ["target_x", "target_y"]

    for col in feature_cols + target_cols:
        if col not in df.columns:
            print(f"Error: Required column '{col}' missing from calibration data.")
            sys.exit(1)

    X = df[feature_cols].values
    y = df[target_cols].values

    results: list[dict] = []

    # ---------------------------------------------------------
    # 1. Level 0: Screen Center Dummy Baseline
    # ---------------------------------------------------------
    center_pred = np.full_like(y, [SCREEN_WIDTH / 2.0, SCREEN_HEIGHT / 2.0])
    res_center = evaluate_predictions(y, center_pred, "Level 0: Screen Center Baseline")
    results.append(res_center)

    # ---------------------------------------------------------
    # 2. Level 1: Direct 2D Gaze Heuristic
    # ---------------------------------------------------------
    # Maps gaze_x [-1, 1] -> [0, 1920], gaze_y [-1, 1] -> [0, 1080]
    heuristic_x = (X[:, 0] + 1.0) / 2.0 * SCREEN_WIDTH
    heuristic_y = (X[:, 1] + 1.0) / 2.0 * SCREEN_HEIGHT
    heuristic_pred = np.column_stack([heuristic_x, heuristic_y])
    res_heuristic = evaluate_predictions(y, heuristic_pred, "Level 1: 2D Gaze Heuristic")
    results.append(res_heuristic)

    # ---------------------------------------------------------
    # 3. Level 2: Trained Random Forest Regressor (spatial_mapper.pkl)
    # ---------------------------------------------------------
    if os.path.exists(args.model_path):
        rf_model = joblib.load(args.model_path)
        rf_pred = rf_model.predict(X)
        res_rf = evaluate_predictions(y, rf_pred, "Level 2: Random Forest (spatial_mapper.pkl)")
        results.append(res_rf)
    else:
        print(f"Warning: Model not found at '{args.model_path}'. Skipping Level 2.")

    # ---------------------------------------------------------
    # 4. Level 3: Degree-2 Polynomial Ridge Regression (5-Fold CV)
    # ---------------------------------------------------------
    poly_pred = fit_and_eval_polynomial_cv(X, y, n_splits=5)
    res_poly = evaluate_predictions(y, poly_pred, "Level 3: Polynomial Ridge (5-Fold CV)")
    results.append(res_poly)

    # ---------------------------------------------------------
    # Format and Display Results Table
    # ---------------------------------------------------------
    print("\n" + "=" * 115)
    print(f"{'Model Architecture':<36} | {'MAE (px)':<9} | {'Median':<8} | {'P95':<8} | {'Hit@25':<7} | {'Hit@50':<7} | {'Hit@100':<8} | {'Visual Ang':<10}")
    print("-" * 115)
    for r in results:
        print(
            f"{r['model']:<36} | "
            f"{r['mae_combined']:>7.1f}px | "
            f"{r['median_euclidean']:>6.1f}px | "
            f"{r['p95_euclidean']:>6.1f}px | "
            f"{r['hit_25px']:>6.1f}% | "
            f"{r['hit_50px']:>6.1f}% | "
            f"{r['hit_100px']:>6.1f}% | "
            f"{r['angular_median_deg']:>8.2f}°"
        )
    print("=" * 115)

    # Save results to CSV
    out_path = Path("data") / "model_evaluation_results.csv"
    pd.DataFrame(results).to_csv(out_path, index=False)
    print(f"\nEmpirical evaluation results saved to: {out_path}")


if __name__ == "__main__":
    main()

