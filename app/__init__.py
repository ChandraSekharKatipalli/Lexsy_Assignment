# app/__init__.py
import os
import google.generativeai as genai
from flask import Flask
from config import Config

# Create the app instance
app = Flask(__name__)
app.config.from_object(Config)

# Configure Gemini
api_key = app.config.get('GEMINI_API_KEY')
if not api_key:
    raise ValueError("GEMINI_API_KEY not found. Set it in your .env file.")
genai.configure(api_key=api_key)

# Create upload/completed folders
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
if not os.path.exists(app.config['COMPLETED_FOLDER']):
    os.makedirs(app.config['COMPLETED_FOLDER'])

# Import routes *after* app is created to avoid circular imports
from app import routes