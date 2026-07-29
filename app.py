from flask import Flask, request, jsonify
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image
import os
import io
import json
import re

load_dotenv()

load_dotenv()

genai.configure(
    api_key=os.getenv("AQ.Ab8RN6Lz361zvr33t9VDBJem1tNYRWXq9kOYnc-4jAvhEzn05w")
)

model = genai.GenerativeModel("gemini-2.5-flash")

app = Flask(__name__)


def extract_json(text):
    text = re.sub(r"```json", "", text)
    text = re.sub(r"```", "", text)
    start = text.find("{")
    end = text.rfind("}")
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
            }),400

        image=request.files["image"]

        img=Image.open(io.BytesIO(image.read()))

        prompt="""
You are an Electrical PPE Inspector.

Check ONLY these PPE items.

1. Arc Flash Suit
2. Arc Flash Face Shield
3. Electrical Gloves
4. Safety Shoes

Rules:

If no person -> false

If PPE not visible -> false

Never guess.

Return ONLY JSON.

Example

{
 "arcFlashSuit": true,
 "faceShield": true,
 "electricalGloves": true,
 "safetyShoes": true
}
"""

        response=model.generate_content([prompt,img])

        answer=response.text

        clean=extract_json(answer)

        result=json.loads(clean)

        result["overallPass"]=(
            result["arcFlashSuit"]
            and
            result["faceShield"]
            and
            result["electricalGloves"]
            and
            result["safetyShoes"]
        )

        return jsonify({
            "success":True,
            "result":result
        })

    except Exception as e:

        return jsonify({
            "success":False,
            "message":str(e)
        }),500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
