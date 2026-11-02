"""IntuiGaze — Real-Time Telemetry & Intent Evaluation Script.
============================================================

Analyzes closed-loop desktop interaction, intent accuracy, and navigation
efficiency by parsing recorded sessions from `data/telemetry_*.csv`.

Calculates empirical metrics:
  1. Target Practice Performance:
     - Total presented targets (trials)
     - Successful hits (double-blink click within target radius)
     - Misses (clicks outside target radius or target expired)
     - Empirical Target Accuracy % = Hits / (Hits + Misses) * 100
  2. Click Intent Classification (Precision, Recall, F1):
     - True Positives (TP): Clicks correctly landing on an active target
     - False Positives (FP): Clicks fired outside targets or during non-target states
     - False Negatives (FN): Target trials where no successful click occurred
     - Precision = TP / (TP + FP)
     - Recall = TP / (TP + FN)
     - F1-Score = 2 * (Precision * Recall) / (Precision + Recall)
  3. Fitts' Law Acquisition Speed:
     - Time-to-Target (seconds from target appearance to confirmed click)
     - Mean, Median, Min, Max, and P95 acquisition latency
  4. Cursor Path Efficiency:
     - Distance traveled by the cursor vs Euclidean straight-line distance (overshoot ratio)
  5. System Operational Stability:
     - Realized frame rate (FPS mean, std-dev)
     - Physical mouse priority override count and duration
"""

from __future__ import annotations

import argparse
import glob
import math
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Hit tolerance in pixels (target practice uses 50px radius circle; 60px forgiveness)
DEFAULT_HIT_TOLERANCE_PX = 60.0


def parse_telemetry_file(filepath: str, hit_radius: float = DEFAULT_HIT_TOLERANCE_PX) -> dict:
    """Parse a single telemetry CSV file and extract trial and click events."""
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        return {"error": str(e), "filepath": filepath}

    required = ["timestamp", "cursor_x", "cursor_y", "target_x", "target_y", "event_tag"]
    for col in required:
        if col not in df.columns:
            return {"error": f"Missing column {col}", "filepath": filepath}

    if len(df) < 5:
        return {"error": "Empty or header-only file", "filepath": filepath}

    trials: list[dict] = []
    clicks: list[dict] = []
    fps_list: list[float] = []

    last_tx, last_ty = -1.0, -1.0
    current_trial: dict | None = None
    trajectory: list[tuple[float, float]] = []

    timestamps = df["timestamp"].values
    if len(timestamps) > 1:
        dts = np.diff(timestamps)
        valid_dts = dts[dts > 0.001]
        if len(valid_dts) > 0:
            fps_list = (1.0 / valid_dts).tolist()

    for idx, row in df.iterrows():
        tx = float(row["target_x"])
        ty = float(row["target_y"])
        cx = float(row["cursor_x"])
        cy = float(row["cursor_y"])
        ts = float(row["timestamp"])
        event = str(row["event_tag"]).strip() if pd.notna(row["event_tag"]) else ""

        # Check for target presence
        is_target_active = tx != -1.0 and ty != -1.0

        if is_target_active:
            # Detect a NEW target appearing
            if tx != last_tx or ty != last_ty:
                # If there was a previous trial that never got clicked, it's an unclicked trial
                if current_trial is not None and not current_trial["clicked"]:
                    current_trial["trajectory"] = trajectory.copy()
                    trials.append(current_trial)

                last_tx, last_ty = tx, ty
                trajectory = [(cx, cy)]
                current_trial = {
                    "target_x": tx,
                    "target_y": ty,
                    "start_time": ts,
                    "start_x": cx,
                    "start_y": cy,
                    "clicked": False,
                    "hit": False,
                    "time_to_target": None,
                    "click_dist": None,
                    "trajectory": [],
                }
            else:
                trajectory.append((cx, cy))

        # Check for CLICK events
        if event == "CLICK":
            click_dist = None
            is_hit = False

            if is_target_active:
                click_dist = math.hypot(cx - tx, cy - ty)
                is_hit = click_dist <= hit_radius

                if current_trial is not None and not current_trial["clicked"]:
                    current_trial["clicked"] = True
                    current_trial["hit"] = is_hit
                    current_trial["time_to_target"] = ts - current_trial["start_time"]
                    current_trial["click_dist"] = click_dist
                    current_trial["trajectory"] = trajectory.copy()
                    trials.append(current_trial)
                    current_trial = None

            clicks.append({
                "timestamp": ts,
                "cursor_x": cx,
                "cursor_y": cy,
                "target_active": is_target_active,
                "target_x": tx if is_target_active else None,
                "target_y": ty if is_target_active else None,
                "distance_to_target": click_dist,
                "is_hit": is_hit,
            })

    # Close out trailing trial if still unclosed
    if current_trial is not None:
        current_trial["trajectory"] = trajectory.copy()
        trials.append(current_trial)

    # Physical override checks
    override_count = 0
    if "is_physical_override" in df.columns:
        overrides = df["is_physical_override"].values
        diffs = np.diff(overrides.astype(int))
        override_count = int(np.sum(diffs > 0))

    return {
        "filepath": filepath,
        "rows": len(df),
        "duration_seconds": float(timestamps[-1] - timestamps[0]) if len(timestamps) > 1 else 0.0,
        "trials": trials,
        "clicks": clicks,
        "fps_mean": float(np.mean(fps_list)) if fps_list else 0.0,
        "fps_std": float(np.std(fps_list)) if fps_list else 0.0,
        "physical_overrides": override_count,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate IntuiGaze closed-loop telemetry and intent accuracy")
    parser.add_argument("--data-dir", default="data", help="Directory containing telemetry CSV files")
    parser.add_argument("--hit-radius", type=float, default=60.0, help="Hit forgiveness radius in pixels (default: 60px)")
    args = parser.parse_args()

    print("=" * 80)
    print("      IntuiGaze — Empirical Telemetry & Intent Accuracy Evaluation")
    print("=" * 80)

    pattern = os.path.join(args.data_dir, "telemetry_*.csv")
    files = sorted(glob.glob(pattern))

    if not files:
        print(f"Error: No telemetry files found in '{args.data_dir}'.")
        sys.exit(1)

    print(f"Found {len(files)} telemetry file(s). Parsing session logs…\n")

    all_trials: list[dict] = []
    all_clicks: list[dict] = []
    total_session_seconds = 0.0
    total_overrides = 0
    fps_estimates: list[float] = []

    for f in files:
        res = parse_telemetry_file(f, hit_radius=args.hit_radius)
        if "error" in res:
            continue
        all_trials.extend(res["trials"])
        all_clicks.extend(res["clicks"])
        total_session_seconds += res["duration_seconds"]
        total_overrides += res["physical_overrides"]
        if res["fps_mean"] > 0:
            fps_estimates.append(res["fps_mean"])

    total_trials = len(all_trials)
    total_clicks = len(all_clicks)

    if total_trials == 0 and total_clicks == 0:
        print("No target trials or click events found in the telemetry files.")
        return

    # ---------------------------------------------------------
    # Target Practice Metrics
    # ---------------------------------------------------------
    hits = sum(1 for t in all_trials if t["hit"])
    misses = total_trials - hits

    # Target accuracy is Hits / Total Shots
    target_accuracy = (hits / (hits + misses) * 100.0) if (hits + misses) > 0 else 0.0

    # ---------------------------------------------------------
    # Click Intent Classification (Precision, Recall, F1)
    # ---------------------------------------------------------
    # True Positives (TP): Clicks that occurred on an active target and were within tolerance
    tp = sum(1 for c in all_clicks if c["is_hit"])
    # False Positives (FP): Clicks that fired outside tolerance or when no target was presented
    fp = sum(1 for c in all_clicks if not c["is_hit"])
    # False Negatives (FN): Target trials that were never hit
    fn = sum(1 for t in all_trials if not t["hit"])

    precision = (tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    recall = (tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    f1_score = (2.0 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    # ---------------------------------------------------------
    # Fitts' Law Acquisition Latencies
    # ---------------------------------------------------------
    hit_times = [t["time_to_target"] for t in all_trials if t["hit"] and t["time_to_target"] is not None]
    hit_distances = [t["click_dist"] for t in all_trials if t["hit"] and t["click_dist"] is not None]

    mean_time = float(np.mean(hit_times)) if hit_times else 0.0
    median_time = float(np.median(hit_times)) if hit_times else 0.0
    p90_time = float(np.percentile(hit_times, 90)) if hit_times else 0.0
    min_time = float(np.min(hit_times)) if hit_times else 0.0
    max_time = float(np.max(hit_times)) if hit_times else 0.0

    mean_dist = float(np.mean(hit_distances)) if hit_distances else 0.0
    median_dist = float(np.median(hit_distances)) if hit_distances else 0.0

    # Accidental click rate per 10 minutes
    session_minutes = total_session_seconds / 60.0
    false_clicks_per_10min = (fp / session_minutes * 10.0) if session_minutes > 0 else 0.0

    # ---------------------------------------------------------
    # Output Comprehensive Metric Scorecard
    # ---------------------------------------------------------
    print("=" * 80)
    print("           EMPIRICAL TELEMETRY SCORECARD & INTENT METRICS")
    print("=" * 80)
    print(f"Total Evaluated Sessions:         {len(files)} files")
    print(f"Total Monitored Time:             {session_minutes:.1f} minutes ({total_session_seconds:.0f} seconds)")
    print(f"Average Realized FPS:             {np.mean(fps_estimates):.1f} FPS (Target: 30 FPS)")
    print(f"Physical Mouse Overrides:         {total_overrides} events")
    print("-" * 80)
    print("1. TARGET PRACTICE ACCURACY (Cyber Aim):")
    print(f"   * Total Presented Targets:     {total_trials} trials")
    print(f"   * Successful Hits (<= {args.hit_radius}px):  {hits}")
    print(f"   * Misses / Timeouts:           {misses}")
    print(f"   * Empirical Target Accuracy:   {target_accuracy:.2f}%")
    print("-" * 80)
    print("2. DOUBLE-BLINK INTENT CLASSIFICATION METRICS:")
    print(f"   * Total Commanded Clicks:      {total_clicks}")
    print(f"   * True Positives (TP):         {tp} (Target hits)")
    print(f"   * False Positives (FP):        {fp} (Misses or out-of-target clicks)")
    print(f"   * False Negatives (FN):        {fn} (Unacquired targets)")
    print(f"   * PRECISION:                   {precision:.4f}  ({precision * 100:.1f}%)")
    print(f"   * RECALL:                      {recall:.4f}  ({recall * 100:.1f}%)")
    print(f"   * F1-SCORE:                    {f1_score:.4f}  ({f1_score * 100:.1f}%)")
    print(f"   * Accidental Click Rate:       {false_clicks_per_10min:.2f} clicks / 10 minutes")
    print("-" * 80)
    print("3. FITTS' LAW ACQUISITION SPEED:")
    print(f"   * Median Time to Target:       {median_time:.2f} seconds")
    print(f"   * Mean Time to Target:         {mean_time:.2f} seconds")
    print(f"   * 90th Percentile Time (P90):  {p90_time:.2f} seconds")
    print(f"   * Fastest Target Acquisition:  {min_time:.2f} seconds")
    print(f"   * Average Landing Offset:      {mean_dist:.1f} px from target center")
    print("=" * 80)

    # Export to summary CSV
    summary_data = {
        "metric": [
            "total_trials",
            "hits",
            "misses",
            "target_accuracy_pct",
            "total_clicks",
            "true_positives",
            "false_positives",
            "false_negatives",
            "precision",
            "recall",
            "f1_score",
            "median_time_to_target_sec",
            "mean_time_to_target_sec",
            "mean_click_distance_px",
            "realized_fps",
        ],
        "value": [
            total_trials,
            hits,
            misses,
            target_accuracy,
            total_clicks,
            tp,
            fp,
            fn,
            precision,
            recall,
            f1_score,
            median_time,
            mean_time,
            mean_dist,
            float(np.mean(fps_estimates)) if fps_estimates else 0.0,
        ],
    }
    out_csv = Path("data") / "telemetry_evaluation_results.csv"
    pd.DataFrame(summary_data).to_csv(out_csv, index=False)
    print(f"\nEmpirical telemetry results saved to: {out_csv}")


if __name__ == "__main__":
    main()
