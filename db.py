import os
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv

load_dotenv()

_client = None


def get_client():
    global _client
    if _client is None:
        uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        _client = MongoClient(uri)
    return _client


def get_db():
    return get_client()["minerais_db"]["minerais"]


def to_str_id(doc):
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


def find_all():
    col = get_db()
    return [to_str_id(d) for d in col.find().sort("created_at", -1)]


def find_by_id(mineral_id):
    col = get_db()
    try:
        doc = col.find_one({"_id": ObjectId(mineral_id)})
        return to_str_id(doc)
    except Exception:
        return None


def insert_mineral(data):
    col = get_db()
    result = col.insert_one(data)
    return str(result.inserted_id)


def update_mineral(mineral_id, data):
    col = get_db()
    col.update_one({"_id": ObjectId(mineral_id)}, {"$set": data})


def delete_mineral(mineral_id):
    col = get_db()
    col.delete_one({"_id": ObjectId(mineral_id)})
