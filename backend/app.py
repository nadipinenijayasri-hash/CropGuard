from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import torch
import numpy as np
from PIL import Image

from transformers import (
    AutoModelForImageClassification,
    CLIPProcessor,
    CLIPModel
)


app = Flask(__name__)
CORS(app)


# ============================================================
# MODEL 1 — CROP DISEASE MODEL
# ============================================================

MODEL_NAME = (
    "linkanjarad/"
    "mobilenet_v2_1.0_224-plant-disease-identification"
)

print("Loading CropGuard AI model...")

model = AutoModelForImageClassification.from_pretrained(
    MODEL_NAME
)

model.eval()

print("CropGuard AI model loaded! 🌱🤖")


# ============================================================
# MODEL 2 — IMAGE VALIDATOR
# ============================================================

print("Loading image validator...")

VALIDATOR_MODEL_NAME = "openai/clip-vit-base-patch32"

validator_processor = CLIPProcessor.from_pretrained(
    VALIDATOR_MODEL_NAME
)

validator_model = CLIPModel.from_pretrained(
    VALIDATOR_MODEL_NAME
)

validator_model.eval()

print("Image validator loaded! 🌱🔍")


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return send_from_directory(
        "..",
        "index.html"
    )


# ============================================================
# FRONTEND FILES
# ============================================================

@app.route("/<path:filename>")
def frontend(filename):

    return send_from_directory(
        "..",
        filename
    )


# ============================================================
# ANALYZE CROP
# ============================================================

@app.route("/analyze", methods=["POST"])
def analyze():

    # --------------------------------------------------------
    # CHECK IMAGE
    # --------------------------------------------------------

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

        # ====================================================
        # OPEN IMAGE
        # ====================================================

        image = Image.open(
            image_file
        ).convert("RGB")


        # ====================================================
        # STEP 1 — IMAGE VALIDATION
        # ====================================================

        validation_prompts = [

            "a clear photo of a crop plant leaf",

            "a clear photo of a healthy plant",

            "a clear photo of a bird",

            "a clear photo of an animal",

            "a clear photo of a person",

            "a photo of a random object"

        ]


        validator_inputs = validator_processor(

            text=validation_prompts,

            images=image,

            return_tensors="pt",

            padding=True

        )


        # ----------------------------------------------------
        # RUN CLIP
        # ----------------------------------------------------

        with torch.no_grad():

            validator_outputs = validator_model(
                **validator_inputs
            )


            validation_scores = (
                validator_outputs
                .logits_per_image[0]
                .softmax(dim=0)
            )


        # ----------------------------------------------------
        # PLANT SCORE
        # ----------------------------------------------------

        plant_score = (

            validation_scores[0].item()

            +

            validation_scores[1].item()

        )


        # ----------------------------------------------------
        # NON-PLANT SCORE
        # ----------------------------------------------------

        non_plant_score = (

            validation_scores[2].item()

            +

            validation_scores[3].item()

            +

            validation_scores[4].item()

            +

            validation_scores[5].item()

        )


        print()
        print("========== IMAGE VALIDATION ==========")

        print(
            "Plant score:",
            round(
                plant_score * 100,
                2
            ),
            "%"
        )

        print(
            "Non-plant score:",
            round(
                non_plant_score * 100,
                2
            ),
            "%"
        )


        # ====================================================
        # REJECT NON-PLANT IMAGE
        # ====================================================

        if plant_score < non_plant_score:

            print(
                "Image rejected: Non-plant image ❌"
            )


            return jsonify({

                "success": True,

                "status": "uncertain",

                "crop": "Unable to identify",

                "disease": "Not a crop image",

                "confidence": round(
                    plant_score * 100,
                    2
                ),

                "severity": "Unknown",

                "risk": "Unknown",

                "message":
                    "Please upload a clear crop or plant image."

            })


        print(
            "Image accepted as plant ✅"
        )


        # ====================================================
        # STEP 2 — PREPARE IMAGE FOR DISEASE MODEL
        # ====================================================

        image_array = np.array(
            image
        )


        image_tensor = torch.tensor(
            image_array
        ).permute(
            2,
            0,
            1
        ).unsqueeze(0).float()


        # ----------------------------------------------------
        # RESIZE
        # ----------------------------------------------------

        image_tensor = torch.nn.functional.interpolate(

            image_tensor,

            size=(224, 224),

            mode="bilinear",

            align_corners=False

        )


        # ----------------------------------------------------
        # CONVERT 0-255 → 0-1
        # ----------------------------------------------------

        image_tensor = (
            image_tensor / 255.0
        )


        # ----------------------------------------------------
        # NORMALIZE
        # ----------------------------------------------------

        mean = torch.tensor(

            [0.5, 0.5, 0.5]

        ).view(
            1,
            3,
            1,
            1
        )


        std = torch.tensor(

            [0.5, 0.5, 0.5]

        ).view(
            1,
            3,
            1,
            1
        )


        image_tensor = (

            image_tensor - mean

        ) / std


        # ====================================================
        # STEP 3 — DISEASE PREDICTION
        # ====================================================

        print()
        print("========== DISEASE MODEL ==========")


        with torch.no_grad():

            outputs = model(
                pixel_values=image_tensor
            )


        # ====================================================
        # PROBABILITIES
        # ====================================================

        probabilities = torch.nn.functional.softmax(

            outputs.logits,

            dim=1

        )


        # ====================================================
        # BEST PREDICTION
        # ====================================================

        confidence, predicted_class = torch.max(

            probabilities,

            dim=1

        )


        predicted_class = (
            predicted_class.item()
        )


        confidence = (
            confidence.item() * 100
        )


        # ====================================================
        # GET RAW LABEL
        # ====================================================

        label = model.config.id2label[
            predicted_class
        ]


        print(
            "RAW MODEL LABEL:",
            label
        )


        print(
            "Disease confidence:",
            round(
                confidence,
                2
            ),
            "%"
        )


        # ====================================================
        # PARSE MODEL LABEL
        # ====================================================

        raw_label = str(
            label
        ).strip()


        # ----------------------------------------------------
        # PLANTVILLAGE STYLE
        #
        # Example:
        #
        # Tomato___healthy
        # Tomato___Bacterial_spot
        # Corn_(maize)___Common_rust
        # ----------------------------------------------------

        if "___" in raw_label:

            parts = raw_label.split(
                "___",
                1
            )


            crop = parts[0].strip()

            disease = parts[1].strip()


        # ----------------------------------------------------
        # OLD STYLE
        #
        # Example:
        #
        # Corn (Maize) with Common Rust
        # ----------------------------------------------------

        elif " with " in raw_label:

            parts = raw_label.split(
                " with ",
                1
            )


            crop = parts[0].strip()

            disease = parts[1].strip()


        # ----------------------------------------------------
        # HEALTHY LABEL
        # ----------------------------------------------------

        elif raw_label.lower().startswith(
            "healthy "
        ):

            crop = raw_label[
                len("Healthy "):
            ].strip()

            disease = (
                "No disease detected"
            )


        else:

            crop = raw_label.strip()

            disease = "Unknown"


        # ====================================================
        # CLEAN CROP NAME
        # ====================================================

        crop = crop.replace(
            "_",
            " "
        )


        crop = crop.replace(
            "  ",
            " "
        ).strip()


        # ====================================================
        # CLEAN DISEASE NAME
        # ====================================================

        disease = disease.replace(
            "_",
            " "
        )


        disease = disease.replace(
            "  ",
            " "
        ).strip()


        # ====================================================
        # HEALTHY DETECTION
        # ====================================================

        disease_lower = disease.lower()


        healthy_words = [

            "healthy",

            "no disease",

            "no disease detected"

        ]


        is_healthy = any(

            word in disease_lower

            for word in healthy_words

        )


        if is_healthy:

            disease = (
                "No disease detected"
            )


        # ====================================================
        # VALID CROP CHECK
        # ====================================================

        valid_crops = [

            "apple",

            "blueberry",

            "cherry",

            "corn",

            "maize",

            "grape",

            "orange",

            "peach",

            "bell pepper",

            "pepper",

            "potato",

            "raspberry",

            "soybean",

            "squash",

            "strawberry",

            "tomato"

        ]


        crop_lower = crop.lower()


        is_valid_crop = any(

            valid_crop in crop_lower

            for valid_crop in valid_crops

        )


        print(
            "Parsed crop:",
            crop
        )


        print(
            "Parsed disease:",
            disease
        )


        print(
            "Valid crop:",
            is_valid_crop
        )


        # ====================================================
        # CONFIDENCE SAFETY CHECK
        # ====================================================

        if confidence < 80:

            print(
                "Disease confidence too low ❌"
            )


            return jsonify({

                "success": True,

                "status": "uncertain",

                "crop": "Unable to identify",

                "disease": "Uncertain result",

                "message":
                    "CropGuard could not confidently identify this image.",

                "confidence": round(
                    confidence,
                    2
                ),

                "severity": "Unknown",

                "risk": "Unknown"

            })


        # ====================================================
        # INVALID CROP
        # ====================================================

        if not is_valid_crop:

            print(
                "Invalid crop label ❌"
            )


            return jsonify({

                "success": True,

                "status": "uncertain",

                "crop": "Unable to identify",

                "disease": "Uncertain result",

                "message":
                    "CropGuard could not identify a supported crop.",

                "confidence": round(
                    confidence,
                    2
                ),

                "severity": "Unknown",

                "risk": "Unknown"

            })


        # ====================================================
        # SET SEVERITY + RISK
        # ====================================================

        if disease == "No disease detected":

            severity = "None"

            risk = "Low"


        elif confidence >= 90:

            severity = "Moderate"

            risk = "High"


        else:

            severity = "Moderate"

            risk = "Medium"


        # ====================================================
        # FINAL RESULT
        # ====================================================

        print()
        print("========== FINAL RESULT ==========")

        print(
            "Crop:",
            crop
        )

        print(
            "Disease:",
            disease
        )

        print(
            "Confidence:",
            round(
                confidence,
                2
            ),
            "%"
        )

        print(
            "Severity:",
            severity
        )

        print(
            "Risk:",
            risk
        )

        print(
            "=================================="
        )


        return jsonify({

            "success": True,

            "status": "success",

            "crop": crop,

            "disease": disease,

            "confidence": round(
                confidence,
                2
            ),

            "severity": severity,

            "risk": risk

        })


    # ========================================================
    # ERROR HANDLING
    # ========================================================

    except Exception as error:

        print()
        print("========== ERROR ==========")

        print(
            "ERROR:",
            error
        )

        print(
            "==========================="
        )


        return jsonify({

            "success": False,

            "message":
                "Could not analyze image."

        }), 500


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )