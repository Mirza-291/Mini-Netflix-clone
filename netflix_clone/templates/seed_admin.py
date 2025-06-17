# seed_admin.py
import bcrypt
from pymongo import MongoClient
from datetime import datetime

# 1) generate hash of your chosen password
raw_pw = b"7890"
pw_hash = bcrypt.hashpw(raw_pw, bcrypt.gensalt()).decode()

# 2) connect & insert
client = MongoClient("mongodb://localhost:27017/")
db = client["mini_netflix"]
db.admins.insert_one({
  "username":      "admin",
  "password_hash": pw_hash,
  "email":         "admin@yourdomain.com",
  "role":          "superuser",
  "created_at":    datetime.utcnow(),
  "last_login":    None
})
client.close()
