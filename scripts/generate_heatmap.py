import glob
import math
import os
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# Screen resolution (hardcoded for now, but should ideally be dynamic)
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

def find_all_datasets(data_dir="data"):
    search_path = os.path.join(data_dir, "telemetry_*.csv")
    files = glob.glob(search_path)
    if not files:
        print(f"No telemetry files found in {data_dir}")
        return []
    return files

def parse_target_hits(df):
    """Parses raw frame-by-frame telemetry into a list of "Hits".
    A Hit is defined as the time between a new target appearing and the user clicking it.
    """
    hits = []

    last_target_x = -1.0
    last_target_y = -1.0
    target_start_time = None
    start_cursor_x = None
    start_cursor_y = None

    # Trajectory of the current attempt
    current_trajectory = []

    for _, row in df.iterrows():
        tx = row['target_x']
        ty = row['target_y']
        cx = row['cursor_x']
        cy = row['cursor_y']
        ts = row['timestamp']
        event = row['event_tag']

        # We only care about frames where a target exists
        if tx != -1 and ty != -1:

            # Detect a NEW target spawning
            if (tx != last_target_x) or (ty != last_target_y):
                last_target_x = tx
                last_target_y = ty
                target_start_time = ts
                start_cursor_x = cx
                start_cursor_y = cy
                current_trajectory = []

            current_trajectory.append((cx, cy))

            # Detect a CLICK
            if event == 'CLICK':
                dist = math.sqrt((cx - tx)**2 + (cy - ty)**2)
                # If they clicked within the target's forgiveness radius (assuming ~60px)
                if dist <= 60:
                    time_taken = ts - target_start_time
                    distance_traveled = math.sqrt((tx - start_cursor_x)**2 + (ty - start_cursor_y)**2)

                    hits.append({
                        'target_x': tx,
                        'target_y': ty,
                        'start_x': start_cursor_x,
                        'start_y': start_cursor_y,
                        'time_to_target': time_taken,
                        'distance_to_target': distance_traveled,
                        'trajectory': current_trajectory.copy()
                    })

                    # Reset so we don't count multiple clicks on the same target
                    last_target_x = -1.0

    return pd.DataFrame(hits)

def generate_visualizations(file_paths) -> None:
    print(f"Aggregating {len(file_paths)} Datasets...")
    dfs = []
    for f in file_paths:
        dfs.append(pd.read_csv(f))

    df = pd.concat(dfs, ignore_index=True)
    print(f"Total Rows Loaded: {len(df)}")

    hits_df = parse_target_hits(df)
    if len(hits_df) == 0:
        print("No successful hits found in dataset.")
        return

    print(f"Extracted {len(hits_df)} successful target hits.")

    # Setup plotting grid
    fig = plt.figure(figsize=(18, 10))
    fig.suptitle('EyeNav Spatial Data & Fitts\'s Law Analysis', fontsize=20)

    # ==========================================
    # Plot 1: Spatial Heatmap (Time to Target)
    # ==========================================
    ax1 = plt.subplot(2, 2, 1)

    # We use a hexbin plot to map the screen into regions and color by 'time_to_target'
    hb = ax1.hexbin(
        hits_df['target_x'],
        hits_df['target_y'],
        C=hits_df['time_to_target'],
        gridsize=15,
        cmap='coolwarm',
        reduce_C_function=np.mean
    )
    ax1.set_xlim(0, SCREEN_WIDTH)
    ax1.set_ylim(SCREEN_HEIGHT, 0) # Invert Y so it matches monitor coordinates (0,0 top left)
    ax1.set_title("Spatial Clearance Difficulty (Time to Target)")
    ax1.set_xlabel("Screen X")
    ax1.set_ylabel("Screen Y")
    cb = fig.colorbar(hb, ax=ax1)
    cb.set_label("Average Time to Hit (Seconds)")

    # ==========================================
    # Plot 2: Fitts's Law Scatter Plot
    # ==========================================
    ax2 = plt.subplot(2, 2, 2)
    sns.regplot(data=hits_df, x='distance_to_target', y='time_to_target', ax=ax2, scatter_kws={'alpha':0.6}, line_kws={'color':'red'})
    ax2.set_title("Fitts's Law: Distance vs Time")
    ax2.set_xlabel("Distance to Target (Pixels)")
    ax2.set_ylabel("Time to Target (Seconds)")

    # ==========================================
    # Plot 3: Cursor Trajectory Maps
    # ==========================================
    ax3 = plt.subplot(2, 1, 2)
    ax3.set_xlim(0, SCREEN_WIDTH)
    ax3.set_ylim(SCREEN_HEIGHT, 0)
    ax3.set_title("Cursor Trajectories (Saccade Smoothness)")
    ax3.set_xlabel("Screen X")
    ax3.set_ylabel("Screen Y")

    # Draw targets
    ax3.scatter(hits_df['target_x'], hits_df['target_y'], color='red', marker='x', s=100, label="Targets")

    # Draw paths
    for _idx, row in hits_df.iterrows():
        path = np.array(row['trajectory'])
        if len(path) > 1:
            ax3.plot(path[:, 0], path[:, 1], alpha=0.3, color='cyan')

    # Remove legends if they get too crowded, or just keep custom entries
    handles, labels = ax3.get_legend_handles_labels()
    by_label = dict(zip(labels, handles, strict=False))
    ax3.legend(by_label.values(), by_label.keys())

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    # Save the figure
    graphs_dir = os.path.join("data", "graphs")
    os.makedirs(graphs_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = os.path.join(graphs_dir, f"heatmap_{timestamp}.png")

    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"\n✅ High-resolution graphs saved to: {save_path}")

    plt.show()

if __name__ == "__main__":
    csv_files = find_all_datasets()
    if csv_files:
        generate_visualizations(csv_files)
