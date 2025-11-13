import os
import base64
import re
from dotenv import load_dotenv
from google.generativeai import GenerativeModel, GenerationConfig

load_dotenv()

def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Gemini client setup
gemini_model = None
if os.getenv("GOOGLE_API_KEY"):
    gemini_model = GenerativeModel('gemini-2.5-pro', generation_config=GenerationConfig(max_output_tokens=128))

def ask_text_to_gemini(image_path, model=None):
    if not gemini_model:
        raise Exception("Gemini API key not configured.")
    prompt = "Act as a blind person assistant. Read the text from the image and give me only the text answer."
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    model_to_use = model if model else 'gemini-2.5-pro'
    response = gemini_model.generate_content([image_bytes, prompt])
    return response.text.strip()

def ask_recaptcha_instructions_to_gemini(image_path, model=None):
    if not gemini_model:
        raise Exception("Gemini API key not configured.")
    prompt = """
    Analyze the blue instruction bar in the image. Identify the primary object the user is asked to select. 
    For example, if it says 'Select all squares with motorcycles', the object is 'motorcycles'. 
    Respond with only the single object name in lowercase. If the instruction is to 'click skip', return 'skip'.
    """
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    model_to_use = model if model else 'gemini-2.5-pro'
    response = gemini_model.generate_content([image_bytes, prompt])
    return response.text.strip().lower()

def ask_if_tile_contains_object_gemini(image_path, object_name, model=None):
    if not gemini_model:
        raise Exception("Gemini API key not configured.")
    prompt = f"Does this image clearly contain a '{object_name}' or a recognizable part of a '{object_name}'? Respond only with 'true' if you are certain. If you are unsure or cannot tell confidently, respond only with 'false'."
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    model_to_use = model if model else 'gemini-2.5-pro'
    response = gemini_model.generate_content([image_bytes, prompt])
    return response.text.strip().lower()