import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import os
import pandas as pd

baseFolder = r"C:\Users\Anant\OneDrive\Desktop\vbn_data\vbn_data"
inputFolder = os.path.join(baseFolder, f"blob_size_data")
csvPath = os.path.join(inputFolder, "led_analysis_summary_moment_3.csv")

df = pd.read_csv(csvPath) 
data_size = df["blob area"].dropna().sort_values(ascending=False).reset_index(drop=True)
data_dis_leds = df["dist bw leds"].dropna().sort_values(ascending=False).reset_index(drop=True)
data_size = data_size[1:]
data_dis_leds = data_dis_leds[1:]
data_distance = []
for i, value in data_size.items():
    data_distance.append(26*i + 30)
    #print(i, value, data_distance[i])

data_distance = np.array(data_distance)
def model(x,k):
    return (k/x)**2 

def model_dis(x,k):
    return k/x

popt, pcov = curve_fit(model, data_distance, data_size.values)
k = popt[0]
print(f"Fitted k value: {k}")

popt, pcov = curve_fit(model_dis, data_distance, data_dis_leds.values)
l = popt[0]
print(f"Fitted l value: {l}")

x_fit = np.linspace(data_distance.min(), data_distance.max(), 100)
y_fit = model(x_fit, k) 
y_expected = model(x_fit, 8046.9)  # Example expected k value
y_actual = data_size.values
plt.figure()
plt.scatter(data_distance, y_actual, label="Actual Data", color='blue')
plt.plot(x_fit, y_fit, label="Fitted Model", color='red')
plt.plot(x_fit, y_expected, label="Expected", color='green')
plt.xlabel("Distance")
plt.ylabel("Blob Area")
plt.title("Blob Size vs Distance with Fitted Model, k={:.2f}".format(k))
plt.legend()
plt.show()
plt.savefig(os.path.join(inputFolder, "blob_size_vs_distance_fit.png"), dpi=200)
plt.close()
x_fit = np.linspace(data_distance.min(), data_distance.max(), 100)
y_fit = model_dis(x_fit, l) 
y_expected = model_dis(x_fit, 9080)  # Example expected k value
y_actual = data_dis_leds.values
plt.figure()
plt.scatter(data_distance, y_actual, label="Actual Data", color='blue')
plt.plot(x_fit, y_fit, label="Fitted Model", color='red')
plt.plot(x_fit, y_expected, label="Expected", color='green')
plt.xlabel("Distance")
plt.ylabel("Distance Between LEDs")
plt.title("Distance Between LEDs vs Distance with Fitted Model, l={:.2f}".format(l))
plt.legend()
plt.show()
plt.savefig(os.path.join(inputFolder, "distance_between_leds_vs_distance_fit.png"), dpi=200)
plt.close()