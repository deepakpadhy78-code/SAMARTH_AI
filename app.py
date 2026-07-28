from flask import Flask, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
import base64
import json
import os
import re

load_dotenv()

client = OpenAI(
    api_key=os.getenv("SAMBANOVA_API_KEY"),
    base_url="https://api.sambanova.ai/v1"
)

app = Flask(__name__)
def extract_json(text):

    text = text.strip()

    text = re.sub(r"```json", "", text)
    text = re.sub(r"```", "", text)

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise Exception("JSON not found")

    return text[start:end + 1]
@app.route("/verifyPPE", methods=["POST"])
def verify_ppe():

    try:

        print("\n========================================")
        print("VERIFY PPE API CALLED")
        print("========================================")

        if "image" not in request.files:

            return jsonify({
                "success": False,
                "message": "No image uploaded"
            }),400

        image=request.files["image"]

        image_bytes=image.read()

        print("Image :",image.filename)
        print("Image Size :",len(image_bytes))

        image_base64=base64.b64encode(image_bytes).decode("utf-8")

        prompt="""
You are an Electrical PPE Inspector.

Look carefully at the uploaded image.

Check ONLY these PPE items.

1. Arc Flash Suit
2. Arc Flash Face Shield
3. Electrical Gloves
4. Safety Shoes

Rules:

- If no person -> false
- If empty room -> false
- If PPE not clearly visible -> false
- Never guess.
- Return ONLY JSON.

Example

{
 "arcFlashSuit":true,
 "faceShield":true,
 "electricalGloves":true,
 "safetyShoes":true
}
"""

        response=client.chat.completions.create(

            model="gemma-4-31B-it",

            temperature=0,

            messages=[

                {
                    "role":"system",
                    "content":"You are a strict Electrical Safety Inspector."
                },

                {
                    "role":"user",
                    "content":[

                        {
                            "type":"text",
                            "text":prompt
                        },

                        {
                            "type":"image_url",
                            "image_url":{
                                "url":f"data:image/jpeg;base64,{image_base64}"
                            }
                        }

                    ]
                }

            ]

        )

        answer=response.choices[0].message.content.strip()

        print("\n=========== AI RESPONSE ===========")
        print(answer)
        print("===================================\n")

        clean_answer=extract_json(answer)

        result=json.loads(clean_answer)

        result["overallPass"]=(
            result.get("arcFlashSuit",False)
            and
            result.get("faceShield",False)
            and
            result.get("electricalGloves",False)
            and
            result.get("safetyShoes",False)
        )

        return jsonify({

            "success":True,
            "result":result

        })

    except Exception as e:

        print(e)

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