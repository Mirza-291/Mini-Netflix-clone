import pandas as pd
from pymongo import MongoClient

# 1) Connect
client = MongoClient("mongodb://localhost:27017/")
db = client["mini_netflix"]
credits_col = db["credits"]

# 2) (Re)create clean collection
credits_col.drop()

# 3) Load & insert
df = pd.read_csv("tmdb_5000_credits.csv")

# If your CSV columns are named movie_id, cast, crew already:
records = df.to_dict(orient="records")
credits_col.insert_many(records)

print(f"Inserted {len(records)} credit documents")
