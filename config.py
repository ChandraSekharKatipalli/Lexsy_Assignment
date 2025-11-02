import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'a-fallback-secret-key-for-dev')
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    GCS_BUCKET_NAME = os.environ.get('GCS_BUCKET_NAME')
    
    UPLOAD_FOLDER = 'uploads'
    COMPLETED_FOLDER = 'completed'