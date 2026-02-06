"""
File extraction utility for extracting payment details from uploaded documents.

Uses OpenAI to extract payee, amount, and purpose from PDFs and images.
"""
import time
import os
import base64
import warnings
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from config import EXTRACTION_MODEL_CONFIG

warnings.filterwarnings("ignore", category=DeprecationWarning)

load_dotenv(override=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_payment_details(file_path: str, file_id: str) -> dict:
    """
    Extract payment details from a file using OpenAI.
    
    For PDFs: Uses Assistants API with file_search
    For Images: Uses vision API
    
    Args:
        file_path: Path to the file
        file_id: OpenAI file ID
        
    Returns:
        dict with extracted payment details or error
    """
    prompt = """Please read this document and extract payment-related details.
    
    Extract the following information if available:
    - Payee (recipient name or business name)
    - Amount (numerical value only remove any currency symbols)
    - Currency (if specified)
    - Purpose or description of the payment
    
    IMPORTANT: Detect the language of the document and respond in that SAME language.
    If the document is in Spanish, respond in Spanish.
    If the document is in French, respond in French.
    If the document is in English, respond in English.
    
    Format your response as a clear summary of these details in the document's language."""
    
    file_extension = Path(file_path).suffix.lower()
    
    try:
        # For images, use vision API
        if file_extension in ['.png', '.jpg', '.jpeg']:
            with open(file_path, 'rb') as f:
                base64_file = base64.b64encode(f.read()).decode('utf-8')
            
            media_type = f"image/{file_extension[1:]}"
            
            response = client.chat.completions.create(
                model=EXTRACTION_MODEL_CONFIG["name"],
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{media_type};base64,{base64_file}"
                                }
                            }
                        ]
                    }
                ],
                temperature=EXTRACTION_MODEL_CONFIG["temperature"]
            )
            
            extracted_content = response.choices[0].message.content
            
            return {
                "success": True,
                "extracted_details": extracted_content,
                "file_type": "image"
            }
        
        # For PDFs, use Assistants API with file_search
        elif file_extension == '.pdf':
            
            assistant = client.beta.assistants.create(
                name="Payment Details Extractor",
                instructions="You are a helpful assistant that extracts payment information from documents.",
                model=EXTRACTION_MODEL_CONFIG["name"],
                tools=[{"type": "file_search"}]
            )
            
            thread = client.beta.threads.create()
            
            client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=prompt,
                attachments=[
                    {
                        "file_id": file_id,
                        "tools": [{"type": "file_search"}]
                    }
                ]
            )
            
            run = client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant.id
            )
            
            while run.status in ["queued", "in_progress"]:
                time.sleep(1)
                run = client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
            
            if run.status == "completed":
                messages = client.beta.threads.messages.list(thread_id=thread.id)
                
                for msg in messages.data:
                    if msg.role == "assistant":
                        extracted_content = msg.content[0].text.value
                        client.beta.assistants.delete(assistant.id)
                        
                        return {
                            "success": True,
                            "extracted_details": extracted_content,
                            "file_type": "pdf"
                        }
            
            client.beta.assistants.delete(assistant.id)
            return {
                "success": False,
                "error": f"Extraction failed with status: {run.status}"
            }
        
        else:
            return {
                "success": False,
                "error": f"Unsupported file type: {file_extension}"
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Extraction error: {str(e)}"
        }
