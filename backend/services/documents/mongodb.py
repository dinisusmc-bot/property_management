from pymongo import MongoClient
from gridfs import GridFS
from config import settings

# MongoDB connection
mongo_client = MongoClient(settings.MONGODB_URL)
mongo_db = mongo_client[settings.MONGODB_DATABASE]

# GridFS for file storage
fs = GridFS(mongo_db)

def get_mongodb():
    """Get MongoDB database instance"""
    return mongo_db

def get_gridfs():
    """Get GridFS instance for file storage"""
    return fs
