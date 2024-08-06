from pypdf import PdfReader
import google.generativeai as genai
import json
import google.ai.generativelanguage as glm
import os
from dotenv import load_dotenv
from io import BytesIO


import typing_extensions as typing

class Card(typing.TypedDict):
    question: str
    answer: str


def generate_flashcards_from_pdf(pdf_filename: BytesIO) -> list[Card]:
    # Extract text from the PDF
    def extract_text_from_pdf(pdf_filename: BytesIO) -> str:
    
        reader = PdfReader(pdf_filename)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text

    text = extract_text_from_pdf(pdf_filename)

    # Load environment variables and configure the API
    load_dotenv()
    genai.configure(api_key=os.getenv("API_KEY"))

    # Define the model and prompt
    model = genai.GenerativeModel('gemini-1.5-pro', generation_config={"response_mime_type": "application/json", "response_schema": list[Card]})
    prompt = f"""
    From the text below, list 10 different flashcards regarding the content
    Using the given JSON schema:
    Text: {text}
    """
    
    # Generate the flashcards
    response = model.generate_content(prompt)
    response_text = response.text

    # Convert the response text to JSON
    flashcards = json.loads(response_text)

    # Format the flashcards
    formatted_flashcards = [{"question": card["question"], "answer": card["answer"]} for card in flashcards]
    
    return formatted_flashcards

# Example usage
'''
pdf_filename = "techari.pdf"
formatted_flashcards = generate_flashcards_from_pdf(pdf_filename)
print(formatted_flashcards)
'''