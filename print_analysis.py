import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import norm

Ranges = [0, 233, 466, 699]
Exposures = [20, 50, 100, 200]

baseFolder = r"C:\Users\Anant\OneDrive\Desktop\vbn_data\vbn_data"
mean_precision = []

for rng in Ranges:
    range_precision = []
    for exp in Exposures:

        inputFolder = os.path.join(baseFolder, f"range_{rng}", f"exp{exp}")
        csvPath = os.path.join(inputFolder, f"led_analysis_summary_moment_3.csv")
        # Change 1 → to whichever index applies

        df = pd.read_csv(csvPath)

        # Pick your desired column name
        data_x = df["gauss_x"].dropna()  
        data_y = df["gauss_y"].dropna()
        x_mean = data_x.mean()
        y_mean = data_y.mean()
        x_dev = data_x.std()
        y_dev = data_y.std()
        cov_xy = np.cov(data_x, data_y)
        # data = pd.Series(dtype=float)
        # for idx in data_x.index:
        #     data[idx] = ((data_x[idx] - x_mean)**2 + (data_y[idx] - y_mean)**2)**0.5    
        # # Stats
        # mu = data.mean()
        # sigma = data.std()
        print (f"Range {rng}, Exposure {exp} → Mean: {x_dev},{y_dev}, Std Dev: {x_dev},{y_dev}, Covariance: {cov_xy[0][1]}")
        if exp == 200:
            mean_precision.append((x_dev, y_dev))
            range_precision.append((x_dev, y_dev))
        # Plot histogram for x
        plt.figure()
        plt.hist(data_x, bins=40, density=True, alpha=0.6)

        # Gaussian
        x = np.linspace(data_x.min(), data_x.max(), 300)
        plt.plot(x, norm.pdf(x, x_mean,x_dev), linewidth=2)

        plt.title(f"Range {rng}, Exposure {exp}")
        plt.xlabel("position in pixels in X")
        plt.ylabel("PDF")

        # Save output figure
        outPath = os.path.join(inputFolder, f"hist_X_gauss_range{rng}_exp{exp}.png")
        plt.savefig(outPath, dpi=200)
        plt.close()
        
        # Plot histogram for y
        plt.figure()
        plt.hist(data_y, bins=40, density=True, alpha=0.6)

        # Gaussian
        x = np.linspace(data_y.min(), data_y.max(), 300)
        plt.plot(x, norm.pdf(x, y_mean,y_dev), linewidth=2)

        plt.title(f"Range {rng}, Exposure {exp}")
        plt.xlabel("position in pixels in Y")
        plt.ylabel("PDF")

        # Save output figure
        outPath = os.path.join(inputFolder, f"hist_Y_gauss_range{rng}_exp{exp}.png")
        plt.savefig(outPath, dpi=200)
        plt.close()


print("\nOverall means for Exposure 200:")
if mean_precision:
    overall_mean_x_dev, overall_mean_y_dev = np.mean(mean_precision, axis=0)
    print(f"Overall Mean x_dev: {overall_mean_x_dev}")
    print(f"Overall Mean y_dev: {overall_mean_y_dev}")