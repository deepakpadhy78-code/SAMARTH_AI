from flask import Flask, request, jsonify
from google import genai
from dotenv import load_dotenv
from PIL import Image
import os
import io
import json
import re
import traceback

# Load environment variables
load_dotenv()

# Gemini Client
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

app = Flask(__name__)


def extract_json(text):
    """Extract JSON object from Gemini response"""
    text = re.sub(r"```json", "", text)
    text = re.sub(r"```", "", text)

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise Exception("Gemini did not return valid JSON.")

    return text[start:end + 1]


@app.route("/")
def home():
    return "SAMARTH AI PPE SERVER RUNNING"
@app.route("/test")
def test():
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Reply with only the word OK"
        )

        return response.text

    except Exception as e:
        import traceback
        traceback.print_exc()
        return str(e), 500


@app.route("/verifyPPE", methods=["POST"])
def verify_ppe():
    try:

        if "image" not in request.files:
            return jsonify({
                "success": False,
                "message": "No image uploaded."
            }), 400

        image_file = request.files["image"]

        img = Image.open(io.BytesIO(image_file.read()))

        prompt = """
You are an Electrical PPE Inspector.

Check ONLY these PPE items:

1. Arc Flash Suit
2. Arc Flash Face Shield
3. Electrical Gloves
4. Safety Shoes

Rules:
- If no person is visible -> false
- If PPE is not clearly visible -> false
- Never guess.
- Return ONLY JSON.

Example:

{
  "arcFlashSuit": true,
  "faceShield": true,
  "electricalGloves": true,
  "safetyShoes": true
}
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt, img]
        )

        answer = response.text

        clean_json = extract_json(answer)

        result = json.loads(clean_json)

        result["overallPass"] = (
            result.get("arcFlashSuit", False)
            and result.get("faceShield", False)
            and result.get("electricalGloves", False)
            and result.get("safetyShoes", False)
        )

        return jsonify({
            "success": True,
            "result": result
        })

    except Exception as e:
        traceback.print_exc()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
