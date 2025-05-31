from google import genai
from pydantic import BaseModel
from typing import List, Dict, Any

# Define input and output models
class HealthData(BaseModel):
    allergies: List[str]
    diabetes: bool
    obesity: bool

class InputPayload(BaseModel):
    mode: str
    user_id: str
    health_data: HealthData
    ingredients: List[str]

# Initialize Gemini client
client = genai.Client(api_key="AIzaSyCXx3iofSsu8Dep8MOaERcv7KX4qYFH1u8")

# Sample input payload
input_data = {
    "mode": "manual",
    "user_id": "test_user",
    "health_data": {
        "allergies": ["nuts"],
        "diabetes": False,
        "obesity": False
    },
    "ingredients": ["chicken", "rice", "broccoli", "garlic", "soy sauce"]
}

parsed_input = InputPayload(**input_data)

# Create prompt for Gemini
prompt = f"""
You are a health-aware recipe assistant.
Recognized ingredients (from AI knowledge) from this list: {parsed_input.ingredients}.
Remove any ingredients containing these allergies: {parsed_input.health_data.allergies}.
Provide 6 healthy recipe suggestions with:
title
ingredients
step-by-step instructions (list)
nutrition info: calories, carbs, and protein

Format your response as JSON with the following schema:
{{
  "recognized_ingredients": [...],
  "filtered_ingredients": [...],
  "recipe_suggestions": [...]
}}
"""

# Generate content
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=prompt,
    config={
        "response_mime_type": "application/json",
    }
)

# Format final output
output = {
    "status": "success",
    "input_mode": parsed_input.mode,
    **eval(response.text),  # Note: replace eval with json.loads after verifying Gemini returns valid JSON
    "feedback_prompt": "Rate these recipes to improve your experience."
}

# Print the output
import json
print(json.dumps(output, indent=2))