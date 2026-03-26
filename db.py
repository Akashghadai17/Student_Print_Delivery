from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["printDB"]
orders = db["orders"]