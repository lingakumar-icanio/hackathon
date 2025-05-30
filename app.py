from flask import Flask, request, jsonify, send_file
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import os

# Initialize Flask app
app = Flask(__name__)

# Gemini API key setup
genai_client = genai.Client(api_key="AIzaSyCXx3iofSsu8Dep8MOaERcv7KX4qYFH1u8")

@app.route('/generate_image', methods=['POST'])
def generate_image():
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
            if hasattr(part, 'text') and part.text is not None:
                text_output += part.text
            elif hasattr(part, 'inline_data') and part.inline_data is not None:
                image_output = Image.open(BytesIO(part.inline_data.data))

        if image_output:
            image_path = "generated_image.png"
            image_output.save(image_path)
            return send_file(image_path, mimetype='image/png')
        else:
            return jsonify({"text": text_output or "No image was generated."})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
