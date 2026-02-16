import pandas as pd
df = pd.read_parquet('data/raw/yellow/yellow_tripdata_2024-01.parquet')
print(df.head())