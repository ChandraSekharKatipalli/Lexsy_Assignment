# app/routes.py
import os
import re
import io
import uuid
import io
import google.cloud.storage
from datetime import timedelta
from flask import (
    render_template, request, redirect, url_for, session, 
    send_file, jsonify
)
from docx import Document
from werkzeug.utils import secure_filename
from app import app  # Import the 'app' object from __init__.py
from app.helpers import generate_smart_question # Import our helper

storage_client = google.cloud.storage.Client()

# --- Homepage Route ---
@app.route('/')
def index():
    return render_template('index.html')

# --- API route for fast upload and preview ---
@app.route('/api/upload-preview', methods=['POST'])
def api_upload_preview():
    if 'document' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['document']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        try:
            filename = secure_filename(file.filename)
            # The 'filepath' is now the name of the object in the bucket
            filepath = f"uploads/{filename}" 
            
            # Get the bucket
            bucket = storage_client.bucket(app.config['GCS_BUCKET_NAME'])
            # Create a "blob" (object) and upload the file
            blob = bucket.blob(filepath)
            blob.upload_from_file(file.stream)

            # Save the GCS path to the session
            session['filepath'] = filepath 
            
            file.stream.seek(0) # Rewind the file stream
            document = Document(file.stream)
            preview_text_list = [para.text for para in document.paragraphs]
            full_preview = "\n".join(preview_text_list)
            
            return jsonify({'preview_text': full_preview})
        
        except Exception as e:
            print(f"Error parsing GCS preview: {e}")
            return jsonify({'error': 'Could not parse .docx file.'}), 500
    
    return jsonify({'error': 'File upload failed.'}), 500

# --- API route for slow AI processing ---
@app.route('/api/process-ai', methods=['GET'])
def api_process_ai():
    filepath = session.get('filepath')
    if not filepath:
        return jsonify({'error': 'No file in session.'}), 400
    
    try:
        bucket = storage_client.bucket(app.config['GCS_BUCKET_NAME'])
        blob = bucket.blob(filepath)

        file_bytes = blob.download_as_bytes()
        file_stream = io.BytesIO(file_bytes)
        
        document = Document(file_stream)


        all_paragraphs = [para.text for para in document.paragraphs]
        full_document_text = "\n".join(all_paragraphs)
        
        print("--- Starting AI question generation in background... ---")
        
        questions = []
        question_id = 0
        for para in document.paragraphs:

            pass
        
        session['questions'] = questions
        session['answers'] = {} 
        
        return jsonify({'status': 'ready'})
    except Exception as e:
  
        pass

# --- Form Filling (Chat) Page ---
@app.route('/fill')
def fill_form():
    filepath = session.get('filepath')
    if not filepath:
        return redirect(url_for('index'))
        
    try:
        # Get the file from GCS
        bucket = storage_client.bucket(app.config['GCS_BUCKET_NAME'])
        blob = bucket.blob(filepath)
        file_bytes = blob.download_as_bytes()
        file_stream = io.BytesIO(file_bytes)

        document = Document(file_stream)
        preview_text_list = [para.text for para in document.paragraphs]
        preview_text = "\n".join(preview_text_list)
    except Exception as e:
        print(f"Error loading preview for chat: {e}")
        preview_text = "Error: Could not load document preview."
    
    return render_template('chat.html', preview_text=preview_text)

# --- API Route for the Chat Interface ---
@app.route('/api/chat', methods=['GET', 'POST'])
def api_chat():
    questions = session.get('questions', [])
    answers = session.get('answers', {})

    if request.method == 'POST':
        data = request.json
        answer = data.get('answer')
        question_id = data.get('id')
        
        if question_id is not None:
            answers[str(question_id)] = answer
            session['answers'] = answers
    
    next_question = None
    for q in questions:
        if str(q['id']) not in answers:
            next_question = q
            break
            
    if next_question:
        return jsonify({
            'status': 'question',
            'question_text': next_question['ai_question'],
            'explanation_text': next_question['ai_explanation'],
            'placeholder': next_question['placeholder'],
            'id': next_question['id'],
            'context': next_question['context']
        })
    else:
        return jsonify({
            'status': 'done',
            'redirect_url': url_for('generate_document')
        })

# --- Document Generation and Download Page ---
@app.route('/download')
def generate_document():
    try:
        filepath = session.get('filepath') # e.g., "uploads/mydoc.docx"
        # ... (get questions and answers) ...

        # Download original file from GCS
        bucket = storage_client.bucket(app.config['GCS_BUCKET_NAME'])
        original_blob = bucket.blob(filepath)
        file_bytes = original_blob.download_as_bytes()
        file_stream = io.BytesIO(file_bytes)
        
        document = Document(file_stream)
        
        # ... (Your placeholder replacement logic is identical) ...

        # --- New Save Logic ---
        final_filename = f"completed_{uuid.uuid4()}.docx"
        final_filepath_in_gcs = f"completed/{final_filename}"
        
        # Save the edited document to a memory stream
        completed_stream = io.BytesIO()
        document.save(completed_stream)
        completed_stream.seek(0)
        
        # Upload the completed file to GCS
        completed_blob = bucket.blob(final_filepath_in_gcs)
        completed_blob.upload_from_file(completed_stream)
        
        # --- (Your preview logic is identical) ---
        completed_stream.seek(0)
        preview_doc = Document(completed_stream)
        preview_text_list = [para.text for para in preview_doc.paragraphs]
        full_preview = "\n".join(preview_text_list)

        return render_template(
            'download.html', 
            preview_text=full_preview, 
            final_filename=final_filepath_in_gcs # Pass the GCS path
        )
    except Exception as e:
        print(f"Error generating document: {e}")
        return "An error occurred while generating your document."

# --- Serves the generated file for download ---
@app.route('/get-file/<path:filename>') # Use <path:> to capture slashes
def get_file(filename):
    try:
        # This no longer sends a file, it sends a secure, temporary URL
        bucket = storage_client.bucket(app.config['GCS_BUCKET_NAME'])
        blob = bucket.blob(filename)
        
        # Create a signed URL valid for 15 minutes
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=15),
            method="GET",
            response_disposition="attachment; filename=completed_document.docx"
        )
        
        # Redirect the user to the secure download link
        return redirect(signed_url)
    except Exception as e:
        print(f"Error generating signed URL: {e}")
        return redirect(url_for('index'))

# --- Lets the user edit their answers ---
@app.route('/edit')
def edit_answers():
    session.pop('answers', None)
    return redirect(url_for('fill_form'))