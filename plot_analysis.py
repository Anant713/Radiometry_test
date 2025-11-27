import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import norm

Ranges = [0, 233, 466, 699]
Exposures = [20, 50, 100, 200]

baseFolder = r"C:\Users\Anant\OneDrive\Desktop\vbn_data\vbn_data"

# Storage for plots
mean_x = {}
mean_y = {}
std_x = {}
std_y = {}

data_x_exp200 = {}
data_y_exp200 = {}

# -------------------------------
# MAIN LOOP: Read all CSVs
# -------------------------------
for rng in Ranges:
    mean_x[rng] = {}
    mean_y[rng] = {}
    std_x[rng] = {}
    std_y[rng] = {}

    for exp in Exposures:

        inputFolder = os.path.join(baseFolder, f"range_{rng}", f"exp{exp}")
        csvPath = os.path.join(inputFolder, "led_analysis_summary_moment_3.csv")

        df = pd.read_csv(csvPath)

        data_x = df["gauss_x"].dropna()
        data_y = df["gauss_y"].dropna()

        mx = data_x.mean()
        my = data_y.mean()
        sx = data_x.std()
        sy = data_y.std()

        mean_x[rng][exp] = mx
        mean_y[rng][exp] = my
        std_x[rng][exp] = sx
        std_y[rng][exp] = sy

        # Collect raw data for exposure=200 histograms later
        if exp == 200:
            data_x_exp200[rng] = data_x
            data_y_exp200[rng] = data_y

        print(f"[OK] Range {rng}, Exposure {exp} → MeanX={mx}, MeanY={my}, StdX={sx}, StdY={sy}")

# ==================================================================================
# 1) STD DEV vs EXPOSURE — one figure, subplots for each range (X + Y)
# ==================================================================================
fig, axs = plt.subplots(2, 2, figsize=(12, 10))
axs = axs.flatten()

for idx, rng in enumerate(Ranges):
    ax = axs[idx]
    xs = [std_x[rng][e] for e in Exposures]
    ys = [std_y[rng][e] for e in Exposures]

    ax.plot(Exposures, xs, marker='o', label='Std X')
    ax.plot(Exposures, ys, marker='o', label='Std Y')

    ax.set_title(f"Std Dev vs Exposure (Range {rng})")
    ax.set_xlabel("Exposure")
    ax.set_ylabel("Std Dev (pixels)")
    ax.grid(True)
    ax.legend()

plt.tight_layout()
plt.savefig("std_vs_exposure_all_ranges.png", dpi=200)
plt.close()

# ==================================================================================
# 2) STD DEV vs RANGE for exposure=200 (single figure)
# ==================================================================================
fig = plt.figure(figsize=(10, 5))

std_x_200 = [std_x[r][200] for r in Ranges]
std_y_200 = [std_y[r][200] for r in Ranges]

plt.plot(Ranges, std_x_200, marker='o', label="Std X")
plt.plot(Ranges, std_y_200, marker='o', label="Std Y")

plt.title("Std Dev vs Range (Exposure = 200)")
plt.xlabel("Range")
plt.ylabel("Std Dev (pixels)")
plt.grid(True)
plt.legend()

plt.tight_layout()
plt.savefig("std_vs_range_exp200.png", dpi=200)
plt.close()

# ==================================================================================
# 3) MEAN vs EXPOSURE — one figure, subplots for each range
# ==================================================================================
# fig, axs = plt.subplots(2, 2, figsize=(12, 10))
# axs = axs.flatten()

# for idx, rng in enumerate(Ranges):
#     ax = axs[idx]

#     mxs = [mean_x[rng][e] for e in Exposures]
#     mys = [mean_y[rng][e] for e in Exposures]

#     ax.plot(Exposures, mxs, marker='o', label='Mean X')
#     ax.plot(Exposures, mys, marker='o', label='Mean Y')

#     ax.set_title(f"Mean vs Exposure (Range {rng})")
#     ax.set_xlabel("Exposure")
#     ax.set_ylabel("Mean position (pixels)")
#     ax.grid(True)
#     ax.legend()

# plt.tight_layout()
# plt.savefig("mean_vs_exposure_all_ranges.png", dpi=200)
# plt.close()

# ==================================================================================
# 4) MEAN vs RANGE for exposure=200
# ==================================================================================
fig = plt.figure(figsize=(10, 5))

mean_x_200 = [mean_x[r][200] for r in Ranges]
mean_y_200 = [mean_y[r][200] for r in Ranges]

plt.plot(Ranges, mean_x_200, marker='o', label="Mean X")
plt.plot(Ranges, mean_y_200, marker='o', label="Mean Y")

plt.title("Mean vs Range (Exposure = 200)")
plt.xlabel("Range")
plt.ylabel("Mean position (pixels)")
plt.grid(True)
plt.legend()

plt.tight_layout()
plt.savefig("mean_vs_range_exp200.png", dpi=200)
plt.close()

# ==================================================================================
# 5) Histogram of dataX and dataY over EXP=200 for ALL RANGES (one figure, subplots)
# ==================================================================================
fig, axs = plt.subplots(2, 2, figsize=(12, 10))
axs = axs.flatten()

for idx, rng in enumerate(Ranges):
    ax = axs[idx]

    dx = data_x_exp200[rng]
    dy = data_y_exp200[rng]
    print (dx.head())
    print (dy.head())

    ax.hist(dx, bins=15, alpha=0.9, label="X")

    ax.set_title(f"Histogram X (Range {rng}, Exp 200)")
    ax.set_xlabel("Position (pixels)")
    ax.set_ylabel("Count")
    ax.legend()
    ax.grid(True)

plt.tight_layout()
plt.savefig("hist_x_exp200_all_ranges.png", dpi=200)
plt.close()

fig, axs = plt.subplots(2, 2, figsize=(12, 10))
axs = axs.flatten()

for idx, rng in enumerate(Ranges):
    ax = axs[idx]

    dx = data_x_exp200[rng]
    dy = data_y_exp200[rng]
    print (dx.head())
    print (dy.head())

    ax.hist(dy, bins=15, alpha=0.9, label="Y")

    ax.set_title(f"Histogram Y (Range {rng}, Exp 200)")
    ax.set_xlabel("Position (pixels)")
    ax.set_ylabel("Count")
    ax.legend()
    ax.grid(True)

plt.tight_layout()
plt.savefig("hist_y_exp200_all_ranges.png", dpi=200)
plt.close()

# ==================================================================================
# NEW: FWHM vs RANGE for ALL exposures on the same plot
# ==================================================================================
fig = plt.figure(figsize=(10, 5))

for exp in Exposures:
    fwhm_vals = []
    for rng in Ranges:
        df = pd.read_csv(os.path.join(
            baseFolder,
            f"range_{rng}",
            f"exp{exp}",
            "led_analysis_summary_moment_3.csv"
        ))
        fwhm_vals.append(df["FWHM_px"].dropna().mean())

    plt.plot(Ranges, fwhm_vals, marker='o', label=f"Exp {exp}")

plt.title("FWHM vs Range for All Exposures")
plt.xlabel("Range")
plt.ylabel("FWHM (pixels)")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig("fwhm_vs_range_all_exposures.png", dpi=200)
plt.close()

print("\nALL PLOTS GENERATED SUCCESSFULLY.")
