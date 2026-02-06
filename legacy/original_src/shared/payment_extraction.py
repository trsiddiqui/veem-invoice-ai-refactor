"""
Document Payment Extraction - Direct Function Implementation
Extracts payment details from documents without MCP server overhead
"""
import asyncio
import base64
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Dict, Optional

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()


def extract_json_from_markdown(content: str) -> str:
    """Extract JSON from markdown code blocks if present."""
    if "```json" in content:
        json_start = content.find("```json") + 7
        json_end = content.find("```", json_start)
        return content[json_start:json_end].strip()
    elif "```" in content:
        json_start = content.find("```") + 3
        json_end = content.find("```", json_start)
        return content[json_start:json_end].strip()
    return content


def create_empty_extraction() -> dict:
    """Return empty extraction structure."""
    return {
        "payee": {"name": None, "email": None},
        "amount": {"value": None, "currency": None},
        "invoice": {"invoice_number": None, "invoice_date": None, "due_date": None}
    }


def extract_from_image(mime_type: str, base64_data: str, prompt: str) -> dict:
    """Extract payment details from an image using Vision API."""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_data}"
                        }
                    }
                ]
            }
        ],
        response_format={"type": "json_object"},
        temperature=0.3
    )
    return json.loads(response.choices[0].message.content)


def extract_from_pdf(file_bytes: bytes, prompt: str) -> dict:
    """Extract payment details from a PDF using Assistants API."""
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
    
    try:
        with open(tmp_path, 'rb') as f:
            file_response = client.files.create(file=f, purpose='assistants')
        file_id = file_response.id
        
        assistant = client.beta.assistants.create(
            name="Payment Extractor",
            instructions=f"You are a helpful assistant that extracts payment details from documents. {prompt}",
            model="gpt-4o",
            tools=[{"type": "file_search"}]
        )
        
        thread = client.beta.threads.create()
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content="Please extract the payment details from the attached document.",
            attachments=[{"file_id": file_id, "tools": [{"type": "file_search"}]}]
        )
        
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id
        )
        
        while run.status in ["queued", "in_progress"]:
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        
        if run.status == "completed":
            messages = client.beta.threads.messages.list(thread_id=thread.id)
            for msg in messages.data:
                if msg.role == "assistant":
                    content = msg.content[0].text.value
                    client.beta.assistants.delete(assistant.id)
                    
                    content = extract_json_from_markdown(content)
                    
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        return create_empty_extraction()
        else:
            client.beta.assistants.delete(assistant.id)
            raise Exception(f"Assistant run failed with status: {run.status}")
    finally:
        os.unlink(tmp_path)


def extract_payment_fields(filename: str, mime_type: str, base64_data: str) -> dict:
    """
    Extract payee, amount, and invoice details from a PDF or image.
    Input file must be base64-encoded bytes.
    """
    try:
        file_bytes = base64.b64decode(base64_data, validate=True)
    except Exception as e:
        raise ValueError(f"Invalid base64_data: {e}")
    
    prompt = (
        "Extract the following payment details from this document:\n"
        "- Payee name and email (if available)\n"
        "- Total amount due and currency\n"
        "- Invoice number, invoice date, and due date (if available)\n\n"
        "Return the data in JSON format with this structure:\n"
        "{\n"
        '  "payee": {"name": "string or null", "email": "string or null"},\n'
        '  "amount": {"value": number or null, "currency": "string or null"},\n'
        '  "invoice": {"invoice_number": "string or null", "invoice_date": "string or null", "due_date": "string or null"}\n'
        "}\n"
    )
    
    if mime_type.startswith('image/'):
        return extract_from_image(mime_type, base64_data, prompt)
    elif mime_type == 'application/pdf':
        return extract_from_pdf(file_bytes, prompt)
    else:
        raise ValueError(f"Unsupported MIME type: {mime_type}")


def extract_payment_details(file_path: str) -> Dict:
    """
    Extract payment details from a document file.
    
    Args:
        file_path: Path to the document file (PDF or image)
    
    Returns:
        dict: Extracted payment details with payee, amount, and invoice
    """
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path_obj, 'rb') as f:
        file_bytes = f.read()
        base64_data = base64.b64encode(file_bytes).decode('utf-8')
    
    suffix = file_path_obj.suffix.lower()
    mime_type_map = {
        '.pdf': 'application/pdf',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
    }
    mime_type = mime_type_map.get(suffix, 'application/octet-stream')
    
    return extract_payment_fields(file_path_obj.name, mime_type, base64_data)
