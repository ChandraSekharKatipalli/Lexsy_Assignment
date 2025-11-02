# app/helpers.py
import re
import json
import google.generativeai as genai

def generate_smart_question(full_document_text, context, placeholder):
    """
    Uses Gemini to turn a legal paragraph into a simple question
    and provide an explanation.
    """
    
    model = genai.GenerativeModel(
        'models/gemini-2.5-flash', # Or your working model name
        generation_config={"response_mime_type": "application/json"}
    )
    
    prompt = f"""
    You are a helpful paralegal. Your job is to make a complex legal document easy to fill out.
    A user needs to provide a value for the placeholder: {placeholder}

    Here is the specific paragraph where it appears:
    "{context}"

    And here is the full text of the entire document, for complete context:
    "{full_document_text}"

    Your task is to generate a JSON object with two keys:
    1. "question": A simple, one-sentence, conversational question for the user.
    2. "explanation": A 2-3 line, simple explanation of *why* this information is needed in the document.

    Example:
    If the placeholder is "[Investor Name]" in the context of "payment by [Investor Name]",
    your response should be:
    {{
      "question": "Who is the investor (the person or company providing the funds)?",
      "explanation": "This identifies the individual or entity making the investment. It is used throughout the document to assign them legal rights and obligations."
    }}

    Now, generate the JSON for the placeholder I provided. Respond *only* with the JSON object.
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text
        
        json_start = text.find('{')
        json_end = text.rfind('}') + 1
        
        if json_start != -1 and json_end != -1:
            clean_text = text[json_start:json_end]
        else:
            clean_text = text
        
        data = json.loads(clean_text) 
        
        return data['question'], data['explanation']
        
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        fallback_q = f"What is the value for {placeholder}?"
        fallback_e = "This is a required field in the document."
        return fallback_q, fallback_e