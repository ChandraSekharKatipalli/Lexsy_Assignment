# app/routes.py
import os
import re
import io
import uuid
from flask import (
    render_template, request, redirect, url_for, session, 
    send_file, jsonify
)
from docx import Document
from werkzeug.utils import secure_filename
from app import app  # Import the 'app' object from __init__.py
from app.helpers import generate_smart_question # Import our helper

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
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            session['filepath'] = filepath
            
            document = Document(filepath)
            preview_text_list = [para.text for para in document.paragraphs]
            full_preview = "\n".join(preview_text_list)
            
            return jsonify({'preview_text': full_preview})
        
        except Exception as e:
            print(f"Error parsing preview: {e}")
            return jsonify({'error': 'Could not parse .docx file.'}), 500
    
    return jsonify({'error': 'File upload failed.'}), 500

# --- API route for slow AI processing ---
@app.route('/api/process-ai', methods=['GET'])
def api_process_ai():
    filepath = session.get('filepath')
    if not filepath:
        return jsonify({'error': 'No file in session.'}), 400
    
    try:
        document = Document(filepath)
        pattern = r'\[.*?\]'
        questions = []
        question_id = 0
        
        all_paragraphs = [para.text for para in document.paragraphs]
        full_document_text = "\n".join(all_paragraphs)
        
        print("--- Starting AI question generation in background... ---")
        
        for para in document.paragraphs:
            found_in_para = re.findall(pattern, para.text)
            for p in found_in_para:
                context = para.text
                ai_question, ai_explanation = generate_smart_question(
                    full_document_text, context, p
                )
                question = {
                    'id': question_id,
                    'placeholder': p,
                    'context': context,
                    'ai_question': ai_question,
                    'ai_explanation': ai_explanation
                }
                questions.append(question)
                question_id += 1
        
        print(f"--- Finished. Found {len(questions)} questions. ---")
        
        session['questions'] = questions
        session['answers'] = {} 
        
        return jsonify({'status': 'ready'})

    except Exception as e:
        print(f"Error generating questions: {e}")
        return jsonify({'error': 'Error calling AI. Check API key/model.'}), 500

# --- Form Filling (Chat) Page ---
@app.route('/fill')
def fill_form():
    filepath = session.get('filepath')
    
    if not filepath:
        return redirect(url_for('index'))
        
    try:
        document = Document(filepath)
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
        filepath = session.get('filepath')
        questions = session.get('questions', [])
        answers = session.get('answers', {})

        if not filepath or not questions or not answers:
            return redirect(url_for('index'))

        document = Document(filepath)
        
        question_index = 0
        total_questions = len(questions)

        for para in document.paragraphs:
            if question_index >= total_questions: break
            current_q = questions[question_index]
            while current_q['placeholder'] in para.text:
                answer = answers.get(str(current_q['id']), '')
                para.text = para.text.replace(current_q['placeholder'], answer, 1)
                question_index += 1
                if question_index >= total_questions: break
                if question_index < total_questions:
                    current_q = questions[question_index]
                else:
                    break

        for table in document.tables:
            for row in table.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        if question_index >= total_questions: break
                        current_q = questions[question_index]
                        while current_q['placeholder'] in para.text:
                            answer = answers.get(str(current_q['id']), '')
                            para.text = para.text.replace(current_q['placeholder'], answer, 1)
                            question_index += 1
                            if question_index >= total_questions: break
                            if question_index < total_questions:
                                current_q = questions[question_index]
                            else:
                                break
                        if question_index >= total_questions: break
                    if question_index >= total_questions: break
                if question_index >= total_questions: break
            if question_index >= total_questions: break
        
        final_filename = f"completed_{uuid.uuid4()}.docx"
        final_filepath = os.path.join(app.config['COMPLETED_FOLDER'], final_filename)
        
        document.save(final_filepath)
        
        preview_text_list = [para.text for para in document.paragraphs]
        full_preview = "\n".join(preview_text_list)

        return render_template(
            'download.html', 
            preview_text=full_preview, 
            final_filename=final_filename
        )

    except Exception as e:
        print(f"Error generating document: {e}")
        return "An error occurred while generating your document."

# --- Serves the generated file for download ---
@app.route('/get-file/<filename>')
def get_file(filename):
    try:
        file_path = os.path.join(app.config['COMPLETED_FOLDER'], filename)
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name='completed_document.docx',
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
    except Exception as e:
        print(f"Error sending file: {e}")
        return redirect(url_for('index'))

# --- Lets the user edit their answers ---
@app.route('/edit')
def edit_answers():
    session.pop('answers', None)
    return redirect(url_for('fill_form'))