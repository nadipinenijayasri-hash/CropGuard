from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import torch
from PIL import Image
from torchvision import transforms
from transformers import AutoModelForImageClassification


app = Flask(__name__)
CORS(app)


# ==============================
# LOAD AI MODEL
# ==============================

MODEL_NAME = "linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification"

print("Loading CropGuard AI model...")

model = AutoModelForImageClassification.from_pretrained(MODEL_NAME)

model.eval()

print("CropGuard AI model loaded! 🌱🤖")


# ==============================
# IMAGE PREPROCESSING
# ==============================

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.5, 0.5, 0.5],
        std=[0.5, 0.5, 0.5]
    )
])


# ==============================
# HOME
# ==============================

@app.route("/")
def home():
    return send_from_directory("..", "index.html")

@app.route("/<path:filename>")
def frontend(filename):
    return send_from_directory("..", filename)


# ==============================
# ANALYZE CROP
# ==============================

@app.route("/analyze", methods=["POST"])
def analyze():

    if "image" not in request.files:
        return jsonify({
            "success": False,
            "message": "No image received"
        }), 400

    image_file = request.files["image"]

    if image_file.filename == "":
        return jsonify({
            "success": False,
            "message": "No image selected"
        }), 400

    try:

        # ==============================
        # OPEN IMAGE
        # ==============================

        image = Image.open(image_file).convert("RGB")


        # ==============================
        # PREPROCESS IMAGE
        # ==============================

        image_tensor = transform(image).unsqueeze(0)


        # ==============================
        # RUN AI PREDICTION
        # ==============================

        with torch.no_grad():

            outputs = model(
                pixel_values=image_tensor
            )


        # ==============================
        # CONVERT TO PROBABILITIES
        # ==============================

        probabilities = torch.nn.functional.softmax(
            outputs.logits,
            dim=1
        )


        # ==============================
        # GET BEST PREDICTION
        # ==============================

        confidence, predicted_class = torch.max(
            probabilities,
            dim=1
        )

        predicted_class = predicted_class.item()

        confidence = confidence.item() * 100

        label = model.config.id2label[predicted_class]


        # ==============================
        # CONFIDENCE SAFETY CHECK
        # ==============================

        if confidence < 80:

            return jsonify({

                "success": True,

                "status": "uncertain",

                "message":
                    "CropGuard could not confidently identify this image.",

                "confidence":
                    round(confidence, 2)

            })


        # ==============================
        # SPLIT CROP + DISEASE
        # ==============================

        if label.startswith("Healthy"):

            crop = label.replace("Healthy ", "")

            disease = "No disease detected"

        else:

            parts = label.split(" with ", 1)

            if len(parts) == 2:

                crop = parts[0]

                disease = parts[1]

            else:

                crop = "Unknown"

                disease = label

        # ==============================
        # SET SEVERITY + RISK
        # ==============================

        if disease == "No disease detected":

            severity = "None"
            risk = "Low"

        elif confidence >= 90:

            severity = "Moderate"
            risk = "High"

        else:

            severity = "Moderate"
            risk = "Medium"

        # ==============================
        # RETURN RESULT
        # ==============================

        return jsonify({

            "success": True,

            "status": "success",

            "crop": crop,

            "disease": disease,

            "confidence":
                round(confidence, 2),

            "severity":
                severity,

            "risk":
                risk

        })


    # ==============================
    # ERROR HANDLING
    # ==============================

    except Exception as error:

        print("ERROR:", error)

        return jsonify({

            "success": False,

            "message":
                "Could not analyze image."

        }), 500


# ==============================
# START SERVER
# ==============================

if __name__ == "__main__":

    app.run(debug=True)