import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

project_root = Path(__file__).resolve().parents[1]
load_dotenv(project_root / ".env")

mongo_client = MongoClient(
    os.environ["MONGODB_URI"],
    serverSelectionTimeoutMS=3000,
)
database = mongo_client[os.environ["MONGODB_DB"]]