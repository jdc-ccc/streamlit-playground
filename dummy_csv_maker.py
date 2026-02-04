import pandas as pd
import numpy as np

# number of rows
n = 400

# create some test data
df = pd.DataFrame({
    "time": np.linspace(0, 10, n),
    "signal": np.sin(np.linspace(0, 10, n)) + 0.1*np.random.randn(n),
    "power_demand": np.gradient(np.sin(np.linspace(0, 10, n))),
    "windspeed": np.random.randint(0,50, n)
})

# save to disk
df.to_csv("dummy_data.csv", index=False)

print("dummy_data.csv created!")
print(df.head())