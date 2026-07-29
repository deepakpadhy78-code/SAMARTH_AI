from flask import Flask, request, jsonify
from google import genai
from PIL import Image
from dotenv import load_dotenv
import os
import io
import json
import re

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)
)

app = Flask(__name__)


def extract_json(text):
    text = re.sub(r"```json", "", text)
    text = re.sub(r"```", "", text)

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise Exception("No JSON returned by Gemini")

    return text[start:end + 1]


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

        img = Image.open(io.BytesIO(image.read()))

        prompt = """
You are an Electrical PPE Inspector.

Check ONLY these PPE items.

1. Arc Flash Suit
2. Arc Flash Face Shield
3. Electrical Gloves
4. Safety Shoes

Rules:

- If no person is visible -> false
- If any PPE item is not clearly visible -> false
- Never guess.

Return ONLY JSON.

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
