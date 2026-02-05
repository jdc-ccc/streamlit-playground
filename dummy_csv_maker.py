import pandas as pd
import numpy as np

# number of rows
n = 400

# create some test data
df = pd.DataFrame({
    "time": np.linspace(0, 10, n),
    "power_demand": np.sin(np.linspace(0, 10, n)) + 0.1*np.random.randn(n),
    "windspeed": np.random.randint(0,50, n)
})

# save to disk
df.to_csv("dummy_power_dataset.csv", index=False)

print("dummy_power_dataset.csv created!")
print(df.head())