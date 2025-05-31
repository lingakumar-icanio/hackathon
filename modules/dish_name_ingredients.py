from google import genai
from pydantic import BaseModel
from typing import List, Dict
import json

# Initialize Gemini client
client = genai.Client(api_key="AIzaSyCXx3iofSsu8Dep8MOaERcv7KX4qYFH1u8")  # Replace with your actual API key

# Define Pydantic models for response validation
class Nutrition(BaseModel):
    calories: int
    carbs: int
    protein: int

class RecipeItem(BaseModel):
    title: str
    ingredients: List[str]
    instructions: List[str]
    nutrition: Nutrition

class RecipeResponse(BaseModel):
    status: str
    input_mode: str
    recognized_ingredients: List[str]
    filtered_ingredients: List[str]
    recipe: List[RecipeItem]
    feedback_prompt: str

# Simulated input payload
input_payload = {
    "mode": "dish",
    "user_id": "test_user",
    "dish_query": "vegetarian pasta primavera"
}

# Build prompt for Gemini
prompt = f"""
Generate a structured JSON response for the following:
Dish query: {input_payload["dish_query"]}
Include:
Recognized ingredients
Filtered ingredients (remove anything non-vegetarian)
Recipe details: title, ingredients, instructions, nutrition (calories, carbs, protein)
A feedback prompt

Ensure the format matches:
status, input_mode, recognized_ingredients, filtered_ingredients, recipe (list of 1), feedback_prompt.
"""

# Call Gemini API
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=prompt,
    config={
        "response_mime_type": "application/json",
        "response_schema": RecipeResponse,
    },
)

# Parse and print result
try:
    parsed_response = RecipeResponse.model_validate_json(response.text)
    print(parsed_response.model_dump_json(indent=2))
except Exception as e:
    print("Failed to parse Gemini response:", e)
    print("Raw response:", response.text)