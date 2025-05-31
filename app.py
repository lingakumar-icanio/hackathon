from flask import Flask, request, jsonify, send_file, url_for
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import os
import base64
import json
from pydantic import BaseModel
from typing import List, Dict, Optional, Any

# Import modules
from modules.image_to_ingredients import extract_ingredients_from_image
from modules.ingre_to_dish import InputPayload, HealthData
from modules.dish_name_ingredients import RecipeResponse

# Initialize Flask app
app = Flask(__name__)

# Gemini API key setup
API_KEY = "AIzaSyCXx3iofSsu8Dep8MOaERcv7KX4qYFH1u8"
genai_client = genai.Client(api_key=API_KEY)

@app.route('/generate_image', methods=['POST'])
def generate_image():
    if not request.is_json:
        return jsonify({"error": "Unsupported Media Type. Use 'Content-Type: application/json'."}), 415

    try:
        # Extract the prompt from the request JSON
        data = request.get_json()
        prompt = data.get("prompt", "Hi, can you create a 3d rendered image of a dish called biriyani")

        # Call Gemini API
        response = genai_client.models.generate_content(
            model="gemini-2.0-flash-preview-image-generation",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=['TEXT', 'IMAGE']
            )
        )

        text_output = ""
        image_output = None

        # Process the response
        for part in response.candidates[0].content.parts:
            if getattr(part, 'text', None):
                text_output += part.text
            elif getattr(part, 'inline_data', None):
                image_output = Image.open(BytesIO(part.inline_data.data))

        if image_output:
            # ✅ Ensure static folder exists
            os.makedirs("static", exist_ok=True)

            # Save image in static folder
            image_filename = "generated_image.png"
            image_path = os.path.join("static", image_filename)
            image_output.save(image_path)

            # Generate full URL for the image
            image_url = url_for('static', filename=image_filename, _external=True)
            return jsonify({
                "image_url": image_url,
                "description": text_output or "Image generated successfully"
            })


        else:
            return jsonify({"text": text_output or "No image was generated."})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
def generate_text_and_image(prompt: str):
    response = client.models.generate_content(
        model="gemini-2.0-flash-preview-image-generation",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=['TEXT', 'IMAGE']
        )
    )

    text_output = ""
    image_output = None

    # ✅ Safely parse parts
    for part in response.candidates[0].content.parts:
        if hasattr(part, 'text') and part.text:
            text_output += part.text.strip()
        elif hasattr(part, 'inline_data') and part.inline_data:
            image_output = Image.open(BytesIO(part.inline_data.data))

    result = {}

    # ✅ Save image and build URL
    if image_output:
        os.makedirs("static", exist_ok=True)
        image_filename = "generated_image.png"
        image_path = os.path.join("static", image_filename)
        image_output.save(image_path)

        image_url = url_for('static', filename=image_filename, _external=True)
        print(f"Image saved at: {image_url}")
        result["image_url"] = image_url

    # ✅ Include text if available
    if text_output:
        result["text"] = text_output

    return json.dumps(result, indent=2)

@app.route('/api/generate-ingredients', methods=['POST'])
def generate_ingredients():
    """
    Handle recipe generation based on different input modes:
    - image: Extract ingredients from image
    - manual: Generate recipes from manually entered ingredients
    - dish: Get ingredients and recipe for a specific dish
    """
    try:
        # Check if the request is form data (for image uploads) or JSON
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Handle form data with image file
            if 'image' not in request.files:
                return jsonify({"error": "No image file provided"}), 400
                
            # Get form data
            image_file = request.files['image']
            user_id = request.form.get('user_id', 'default_user')
            
            # Create data dictionary for image mode
            data = {
                "mode": "image",
                "user_id": user_id,
                "image_file": image_file
            }
            
            # Process image mode
            return handle_image_mode(data)
        else:
            # Handle JSON data for other modes
            if not request.is_json:
                return jsonify({"error": "Unsupported Media Type. Use 'Content-Type: application/json' or 'multipart/form-data'."}), 415
                
            data = request.get_json()
            mode = data.get("mode")
            
            if mode == "image":
                return handle_image_mode(data)
            elif mode == "manual":
                return handle_manual_mode(data)
            elif mode == "dish":
                return handle_dish_query_mode(data)
            else:
                return jsonify({"error": "Invalid mode specified"}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def handle_image_mode(data):
    """Process image mode: extract ingredients from image"""
    user_id = data.get("user_id", "default_user")
    
    try:
        # Determine if we're receiving a file or base64 data
        if "image_file" in data:
            # Handle file upload from form data
            image_file = data["image_file"]
            
            # Save temporarily
            temp_image_path = os.path.join("static", f"temp_{user_id}.jpg")
            os.makedirs("static", exist_ok=True)
            image_file.save(temp_image_path)
            
        elif "image_base64" in data:
            # Handle base64 image data from JSON
            image_base64 = data.get("image_base64")
            
            if not image_base64:
                return jsonify({"error": "No image data provided"}), 400
                
            # Remove base64 prefix if present
            if "base64," in image_base64:
                image_base64 = image_base64.split("base64,")[1]
            
            # Decode base64 to image
            image_data = base64.b64decode(image_base64)
            
            # Save temporarily
            temp_image_path = os.path.join("static", f"temp_{user_id}.jpg")
            os.makedirs("static", exist_ok=True)
            
            with open(temp_image_path, "wb") as f:
                f.write(image_data)
        else:
            return jsonify({"error": "No image provided"}), 400
        
        # Extract ingredients
        ingredients_json = extract_ingredients_from_image(temp_image_path, API_KEY)
        ingredients = json.loads(ingredients_json).get("ingredients", [])
        
        # Clean up temp file
        os.remove(temp_image_path)
        
        # Return just the ingredients list as specified
        return jsonify({
            "ingredients": ingredients
        })
        
    except Exception as e:
        return jsonify({"error": f"Image processing error: {str(e)}"}), 500

def handle_manual_mode(data):
    """Process manual mode: generate recipes from manually entered ingredients"""
    ingredients = data.get("ingredients", [])
    user_id = data.get("user_id")
    health_data = data.get("health_data", {})
    
    if not ingredients:
        return jsonify({"error": "No ingredients provided"}), 400
    
    try:
        # Generate recipes based on ingredients
        model = genai_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=create_recipe_prompt(data),
            config={
                "response_mime_type": "application/json",
            }
        )
        
        # Process model response
        recipe_suggestions = json.loads(model.text)
        # for recipe in recipe_suggestions:
        #     result = generate_text_and_image(recipe["data"])
        #     if "image_url" in result:
        #         recipe["image"] = result["image_url"]
        # Format final response
        response = {
            "status": "success",
            "input_mode": "manual",
            "recognized_ingredients": ingredients,
            "filtered_ingredients": recipe_suggestions.get("filtered_ingredients", []),
            "recipe_suggestions": recipe_suggestions.get("recipe_suggestions", []),
            "feedback_prompt": "Rate these recipes to improve your experience."
        }

        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"error": f"Recipe generation error: {str(e)}"}), 500

def handle_dish_query_mode(data):
    """Process dish query mode: get ingredients and recipe for a specific dish"""
    dish_query = data.get("dish_query")
    user_id = data.get("user_id")
    
    if not dish_query:
        return jsonify({"error": "No dish query provided"}), 400
    
    try:
        # Build prompt for Gemini
        prompt = f"""
        Generate a structured JSON response for the following:
        Dish query: {dish_query}
        Include:
        Recognized ingredients
        Filtered ingredients (remove anything that could be allergenic)
        Recipe details: title, ingredients, instructions, nutrition (calories, carbs, protein)
        A feedback prompt

        Ensure the format matches:
        {{
          "recognized_ingredients": [...],
          "filtered_ingredients": [...],
          "recipe": [
            {{
              "title": "string",
              "ingredients": ["string", ...],
              "instructions": ["string", ...],
              "nutrition": {{
                "calories": number,
                "carbs": number,
                "protein": number
              }}
            }}
          ]
        }}
        """
        
        # Call Gemini API
        model = genai_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
            }
        )
        
        # Process model response
        recipe_data = json.loads(model.text)
        # for recipe in recipe_data:
        #     result = generate_text_and_image(recipe["data"])
        #     if "image_url" in result:
        #         recipe["image"] = result["image_url"]
        # Format final response
        response = {
            "status": "success",
            "input_mode": "dish",
            "recognized_ingredients": recipe_data.get("recognized_ingredients", []),
            "filtered_ingredients": recipe_data.get("filtered_ingredients", []),
            "recipe": recipe_data.get("recipe", []),
            "feedback_prompt": "Rate these recipes to improve your experience."
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"error": f"Dish query error: {str(e)}"}), 500

def create_recipe_prompt(data):
    """Create prompt for recipe generation based on ingredients and health data"""
    ingredients = data.get("ingredients", [])
    health_data = data.get("health_data", {})
    allergies = health_data.get("allergies", [])
    diabetes = health_data.get("diabetes", False)
    obesity = health_data.get("obesity", False)
    
    prompt = f"""
    You are a health-aware recipe assistant.
    Recognized ingredients (from AI knowledge) from this list: {ingredients}.
    Remove any ingredients containing these allergies: {allergies}.
    
    {"Create lower-carb recipes suitable for diabetic patients." if diabetes else ""}
    {"Create lower-calorie recipes to assist with weight management." if obesity else ""}
    
    Provide 3 healthy recipe suggestions with:
    title
    ingredients
    step-by-step instructions (list)
    nutrition info: calories, carbs, and protein

    Format your response as JSON with the following schema:
    {{
      "recognized_ingredients": [...],
      "filtered_ingredients": [...],
      "recipe_suggestions": [
        {{
          "title": "string",
          "ingredients": ["string", ...],
          "instructions": ["string", ...],
          "nutrition": {{
            "calories": number,
            "carbs": number,
            "protein": number
          }}
        }}
      ]
    }}
    """
    
    return prompt

# Run the Flask app
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)