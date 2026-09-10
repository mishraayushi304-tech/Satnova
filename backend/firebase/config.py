import os
import firebase_admin
from firebase_admin import credentials, firestore, storage
from utils.logger import logger

_db_client = None
_bucket_client = None

def initialize_firebase():
    """
    Initializes Firebase Admin SDK if service account key is available.
    Fails gracefully for local offline development.
    """
    global _db_client, _bucket_client
    
    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase/serviceAccountKey.json")
    bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET", "satquery-ai.appspot.com")
    
    if os.path.exists(cred_path):
        try:
            cred = credentials.Certificate(cred_path)
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred, {
                    'storageBucket': bucket_name
                })
            _db_client = firestore.client()
            _bucket_client = storage.bucket()
            logger.info("Firebase Admin SDK successfully initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin SDK: {str(e)}")
    else:
        logger.warning(
            f"Firebase service account key not found at '{cred_path}'. "
            "Running in local mode without Firebase features."
        )

def get_db():
    return _db_client

def get_storage_bucket():
    return _bucket_client
