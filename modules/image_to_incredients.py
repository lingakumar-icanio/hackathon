from google.genai import types
from pydantic import BaseModel
import google.generativeai as genai
import os

class IngredientsResponse(BaseModel):
    ingredients: list[str]

def extract_ingredients_from_image(image_path, api_key):
    """
    Extract ingredients from an image and return as structured JSON
    
    Args:
        image_path (str): Path to the image file
        api_key (str): Google API key for Gemini
    
    Returns:
        dict: JSON object with ingredients list
    """
    
    # Initialize the client
    genai.configure(api_key=api_key)
    
    # Read the image file
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    # Generate content with structured output
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    # Create a content list with image and text prompt
    content = [
        {
            "mime_type": "image/jpeg",
            "data": image_bytes
        },
        {
            "text": "Identify all the food ingredients visible in this image. Return only the ingredient names as a list."
        }
    ]
    
    # Generate response
    response = model.generate_content(
        content,
        generation_config={
            "response_mime_type": "application/json",
            "response_schema": IngredientsResponse,
        }
    )
    
    # Return the structured response
    return response.text

# Example usage
if __name__ == "__main__":
    # Replace with your actual API key and image path
    API_KEY = "AIzaSyCXx3iofSsu8Dep8MOaERcv7KX4qYFH1u8"
    IMAGE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "/home/icanio-10113/Recipe_creator/1685519127-chef-preparing-food-ingredients-2021-09-24-03-57-22-utc (1).webp")
    
    try:
        result = extract_ingredients_from_image(IMAGE_PATH, API_KEY)
        print(result)  # This will output: {"ingredients": ["ingredient1", "ingredient2", ...]}
        
    except Exception as e:
        print(f"Error: {e}")