from flask import Flask, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
from PIL import Image
import os
import io
import json
import re
import base64

load_dotenv()

client = OpenAI(
    api_key=os.getenv("SAMBANOVA_API_KEY"),
    base_url="https://api.sambanova.ai/v1"
)

app = Flask(__name__)


def extract_json(text):
    text = re.sub(r"```json", "", text)
    text = re.sub(r"```", "", text)

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise Exception("No JSON found.")

    return text[start:end+1]


@app.route("/")
def home():
    return "SAMARTH AI PPE SERVER RUNNING"


@app.route("/verifyPPE", methods=["POST"])
def verify_ppe():

    try:

        if "image" not in request.files:
            return jsonify({
                "success": False,
                "message": "No image uploaded"
            }), 400

        image = request.files["image"]

image_bytes = image.read()

# Open image
img = Image.open(io.BytesIO(image_bytes))

# Resize image (reduces payload size)
img.thumbnail((1024, 1024))

# Save compressed image
buffer = io.BytesIO()
img.save(buffer, format="JPEG", quality=85)

# Convert compressed image to Base64
image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        prompt = """
You are an Electrical PPE Inspector.

Check ONLY these PPE items.

1. Arc Flash Suit
2. Arc Flash Face Shield
3. Electrical Gloves
4. Safety Shoes

Rules:
- If no person is visible -> false
- If PPE not visible -> false
- Never guess.

Return ONLY JSON.

{
 "arcFlashSuit": true,
 "faceShield": true,
 "electricalGloves": true,
 "safetyShoes": true
}
"""

        response = client.chat.completions.create(
            model="gemma-4-31B-it",
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
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            temperature=0
        )

        answer = response.choices[0].message.content

        clean = extract_json(answer)

        result = json.loads(clean)

        result["overallPass"] = (
            result["arcFlashSuit"]
            and result["faceShield"]
            and result["electricalGloves"]
            and result["safetyShoes"]
        )

        return jsonify({
            "success": True,
            "result": result
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
