# from flask import Flask, request, jsonify, send_from_directory
# from flask_cors import CORS

# import os
# import torch
# import numpy as np
# from PIL import Image

# from transformers import (
#     AutoModelForImageClassification,
#     CLIPProcessor,
#     CLIPModel
# )


# # ============================================================
# # FLASK APP
# # ============================================================

# app = Flask(__name__)
# CORS(app)


# # ============================================================
# # MODEL 1 — CROP DISEASE MODEL
# # ============================================================

# MODEL_NAME = (
#     "linkanjarad/"
#     "mobilenet_v2_1.0_224-plant-disease-identification"
# )

# print("Loading CropGuard AI model...")

# model = AutoModelForImageClassification.from_pretrained(
#     MODEL_NAME
# )

# model.eval()

# print("CropGuard AI model loaded! 🌱🤖")


# # ============================================================
# # MODEL 2 — CLIP LEAF VALIDATOR
# # ============================================================

# print("Loading image validator...")

# VALIDATOR_MODEL_NAME = "openai/clip-vit-base-patch32"


# validator_processor = CLIPProcessor.from_pretrained(
#     VALIDATOR_MODEL_NAME
# )


# validator_model = CLIPModel.from_pretrained(
#     VALIDATOR_MODEL_NAME
# )

# validator_model.eval()

# print("Image validator loaded! 🌱🔍")


# # ============================================================
# # SUPPORTED CROPS
# # ============================================================

# SUPPORTED_CROPS = [

#     "apple",
#     "blueberry",
#     "cherry",
#     "corn",
#     "maize",
#     "grape",
#     "orange",
#     "peach",
#     "bell pepper",
#     "pepper",
#     "potato",
#     "raspberry",
#     "soybean",
#     "squash",
#     "strawberry",
#     "tomato"

# ]


# # ============================================================
# # BASE DIRECTORY
# # ============================================================

# BASE_DIR = os.path.dirname(
#     os.path.dirname(
#         os.path.abspath(__file__)
#     )
# )


# # ============================================================
# # HOME
# # ============================================================

# @app.route("/")
# def home():

#     return send_from_directory(
#         BASE_DIR,
#         "index.html"
#     )


# # ============================================================
# # FRONTEND FILES
# # ============================================================

# @app.route("/<path:filename>")
# def frontend(filename):

#     return send_from_directory(
#         BASE_DIR,
#         filename
#     )


# # ============================================================
# # CLEAN CROP NAME
# # ============================================================

# def clean_crop_name(crop):

#     crop = str(crop)

#     crop = crop.replace(
#         "_",
#         " "
#     )

#     crop = crop.replace(
#         "(",
#         ""
#     )

#     crop = crop.replace(
#         ")",
#         ""
#     )

#     crop = crop.replace(
#         "  ",
#         " "
#     )

#     crop = crop.strip()


#     # --------------------------------------------------------
#     # Normalize corn / maize
#     # --------------------------------------------------------

#     if "corn" in crop.lower():

#         return "Maize"


#     if "maize" in crop.lower():

#         return "Maize"


#     return crop


# # ============================================================
# # CHECK SUPPORTED CROP
# # ============================================================

# def is_supported_crop(crop):

#     crop_lower = crop.lower()


#     for supported in SUPPORTED_CROPS:

#         if supported in crop_lower:

#             return True


#     return False


# # ============================================================
# # ANALYZE IMAGE
# # ============================================================

# @app.route(
#     "/analyze",
#     methods=["POST"]
# )

# def analyze():


#     # ========================================================
#     # CHECK IMAGE
#     # ========================================================

#     if "image" not in request.files:

#         return jsonify({

#             "success": False,

#             "message":
#                 "No image received."

#         }), 400


#     image_file = request.files["image"]


#     if image_file.filename == "":

#         return jsonify({

#             "success": False,

#             "message":
#                 "No image selected."

#         }), 400


#     try:


#         # ====================================================
#         # OPEN IMAGE
#         # ====================================================

#         image = Image.open(
#             image_file
#         ).convert("RGB")


#         # ====================================================
#         # STEP 1 — LEAF VALIDATION
#         # ====================================================

#         print()
#         print(
#             "========== IMAGE VALIDATION =========="
#         )


#         validation_prompts = [

#             # LEAF CATEGORIES
#             "a close up photograph of a crop leaf",

#             "a close up photograph of a plant leaf",

#             "a photograph of a diseased crop leaf",

#             "a photograph of a healthy crop leaf",

#             # NON-LEAF CATEGORIES
#             "a photograph of a whole plant",

#             "a photograph of a fruit or vegetable",

#             "a photograph of a bird",

#             "a photograph of an animal",

#             "a photograph of a person",

#             "a photograph of a random object"

#         ]


#         # ----------------------------------------------------
#         # CLIP PROCESSING
#         # ----------------------------------------------------

#         validator_inputs = validator_processor(

#             text=validation_prompts,

#             images=image,

#             return_tensors="pt",

#             padding=True

#         )


#         # ----------------------------------------------------
#         # CLIP PREDICTION
#         # ----------------------------------------------------

#         with torch.no_grad():

#             validator_outputs = validator_model(
#                 **validator_inputs
#             )


#             logits = (
#                 validator_outputs
#                 .logits_per_image[0]
#             )


#             probabilities = torch.softmax(
#                 logits,
#                 dim=0
#             )


#         # ====================================================
#         # LEAF SCORE
#         # ====================================================

#         leaf_indices = [

#             0,
#             1,
#             2,
#             3

#         ]


#         # ====================================================
#         # NON-LEAF SCORE
#         # ====================================================

#         non_leaf_indices = [

#             4,
#             5,
#             6,
#             7,
#             8,
#             9

#         ]


#         leaf_score = sum(

#             probabilities[i].item()

#             for i in leaf_indices

#         )


#         non_leaf_score = sum(

#             probabilities[i].item()

#             for i in non_leaf_indices

#         )


#         print(
#             "Leaf score:",
#             round(
#                 leaf_score * 100,
#                 2
#             ),
#             "%"
#         )


#         print(
#             "Non-leaf score:",
#             round(
#                 non_leaf_score * 100,
#                 2
#             ),
#             "%"
#         )


#         # ====================================================
#         # BEST CATEGORY
#         # ====================================================

#         best_index = torch.argmax(
#             probabilities
#         ).item()


#         print(
#             "Best validation category:",
#             validation_prompts[best_index]
#         )


#         # ====================================================
#         # LEAF DECISION
#         # ====================================================

#         #
#         # We require:
#         #
#         # 1. Leaf score > non-leaf score
#         #
#         # AND
#         #
#         # 2. Leaf score should be reasonably strong
#         #
#         #


#         is_leaf = (

#             leaf_score > non_leaf_score

#             and

#             leaf_score >= 0.35

#         )


#         # ====================================================
#         # NOT A LEAF
#         # ====================================================

#         if not is_leaf:

#             print(
#                 "Image rejected: Not a crop leaf ❌"
#             )


#             return jsonify({

#                 "success": True,

#                 "status": "invalid",

#                 "is_leaf": False,

#                 "crop":
#                     "Unable to identify",

#                 "disease":
#                     "Not a crop leaf",

#                 "confidence":
#                     round(
#                         leaf_score * 100,
#                         2
#                     ),

#                 "severity":
#                     "Unknown",

#                 "risk":
#                     "Unknown",

#                 "message":
#                     "Please upload a clear crop leaf image."

#             })


#         # ====================================================
#         # LEAF ACCEPTED
#         # ====================================================

#         print(
#             "Image accepted as crop leaf ✅"
#         )


#         # ====================================================
#         # STEP 2 — PREPARE IMAGE
#         # ====================================================

#         image_array = np.array(
#             image
#         )


#         image_tensor = torch.tensor(
#             image_array
#         ).permute(
#             2,
#             0,
#             1
#         ).unsqueeze(0).float()


#         # ====================================================
#         # RESIZE
#         # ====================================================

#         image_tensor = torch.nn.functional.interpolate(

#             image_tensor,

#             size=(224, 224),

#             mode="bilinear",

#             align_corners=False

#         )


#         # ====================================================
#         # NORMALIZE 0-255 → 0-1
#         # ====================================================

#         image_tensor = (
#             image_tensor / 255.0
#         )


#         # ====================================================
#         # NORMALIZATION
#         # ====================================================

#         mean = torch.tensor(

#             [0.5, 0.5, 0.5]

#         ).view(
#             1,
#             3,
#             1,
#             1
#         )


#         std = torch.tensor(

#             [0.5, 0.5, 0.5]

#         ).view(
#             1,
#             3,
#             1,
#             1
#         )


#         image_tensor = (

#             image_tensor - mean

#         ) / std


#         # ====================================================
#         # STEP 3 — DISEASE MODEL
#         # ====================================================

#         print()
#         print(
#             "========== DISEASE MODEL =========="
#         )


#         with torch.no_grad():

#             outputs = model(
#                 pixel_values=image_tensor
#             )


#         # ====================================================
#         # DISEASE PROBABILITIES
#         # ====================================================

#         disease_probabilities = torch.softmax(

#             outputs.logits,

#             dim=1

#         )


#         # ====================================================
#         # BEST DISEASE
#         # ====================================================

#         confidence, predicted_class = torch.max(

#             disease_probabilities,

#             dim=1

#         )


#         predicted_class = (
#             predicted_class.item()
#         )


#         confidence = (
#             confidence.item() * 100
#         )


#         # ====================================================
#         # MODEL LABEL
#         # ====================================================

#         label = model.config.id2label[
#             predicted_class
#         ]


#         raw_label = str(
#             label
#         ).strip()


#         print(
#             "RAW MODEL LABEL:",
#             raw_label
#         )


#         print(
#             "Disease confidence:",
#             round(
#                 confidence,
#                 2
#             ),
#             "%"
#         )


#         # ====================================================
#         # PARSE MODEL LABEL
#         # ====================================================

#         crop = ""
#         disease = ""


#         # ----------------------------------------------------
#         # FORMAT:
#         #
#         # Tomato___healthy
#         # Tomato___Bacterial_spot
#         # Corn_(maize)___Common_rust
#         #
#         # ----------------------------------------------------

#         if "___" in raw_label:

#             parts = raw_label.split(
#                 "___",
#                 1
#             )


#             crop = parts[0].strip()

#             disease = parts[1].strip()


#         # ----------------------------------------------------
#         # FORMAT:
#         #
#         # Tomato with Early Blight
#         #
#         # ----------------------------------------------------

#         elif " with " in raw_label:

#             parts = raw_label.split(
#                 " with ",
#                 1
#             )


#             crop = parts[0].strip()

#             disease = parts[1].strip()


#         # ----------------------------------------------------
#         # FORMAT:
#         #
#         # Healthy Tomato
#         #
#         # ----------------------------------------------------

#         elif raw_label.lower().startswith(
#             "healthy "
#         ):

#             crop = raw_label[
#                 len("Healthy "):
#             ].strip()


#             disease = (
#                 "No disease detected"
#             )


#         # ----------------------------------------------------
#         # UNKNOWN FORMAT
#         # ----------------------------------------------------

#         else:

#             crop = raw_label.strip()

#             disease = "Unknown"


#         # ====================================================
#         # CLEAN CROP
#         # ====================================================

#         crop = clean_crop_name(
#             crop
#         )


#         # ====================================================
#         # CLEAN DISEASE
#         # ====================================================

#         disease = disease.replace(
#             "_",
#             " "
#         )


#         disease = disease.replace(
#             "  ",
#             " "
#         ).strip()


#         # ====================================================
#         # HEALTHY DETECTION
#         # ====================================================

#         disease_lower = (
#             disease.lower()
#         )


#         if (

#             "healthy" in disease_lower

#             or

#             "no disease" in disease_lower

#         ):

#             disease = (
#                 "No disease detected"
#             )


#         # ====================================================
#         # SUPPORTED CROP CHECK
#         # ====================================================

#         supported = is_supported_crop(
#             crop
#         )


#         print(
#             "Parsed crop:",
#             crop
#         )


#         print(
#             "Parsed disease:",
#             disease
#         )


#         print(
#             "Supported crop:",
#             supported
#         )


#         # ====================================================
#         # UNSUPPORTED CROP
#         # ====================================================

#         if not supported:

#             print(
#                 "Leaf detected but crop unsupported ⚠️"
#             )


#             return jsonify({

#                 "success": True,

#                 "status":
#                     "unsupported",

#                 "is_leaf": True,

#                 "crop":
#                     crop
#                     if crop
#                     else
#                     "Leaf detected",

#                 "disease":
#                     "Crop not supported",

#                 "confidence":
#                     round(
#                         confidence,
#                         2
#                     ),

#                 "severity":
#                     "Unknown",

#                 "risk":
#                     "Unknown",

#                 "message":
#                     "A leaf was detected, but this crop is not currently supported by CropGuard."

#             })


#         # ====================================================
#         # LOW DISEASE CONFIDENCE
#         # ====================================================

#         if confidence < 80:

#             print(
#                 "Disease confidence too low ❌"
#             )


#             return jsonify({

#                 "success": True,

#                 "status":
#                     "uncertain",

#                 "is_leaf": True,

#                 "crop":
#                     crop,

#                 "disease":
#                     "Uncertain result",

#                 "confidence":
#                     round(
#                         confidence,
#                         2
#                     ),

#                 "severity":
#                     "Unknown",

#                 "risk":
#                     "Unknown",

#                 "message":
#                     "CropGuard could not confidently identify the condition."

#             })


#         # ====================================================
#         # SEVERITY + RISK
#         # ====================================================

#         if disease == "No disease detected":

#             severity = "None"

#             risk = "Low"


#         elif confidence >= 90:

#             severity = "Moderate"

#             risk = "High"


#         else:

#             severity = "Moderate"

#             risk = "Medium"


#         # ====================================================
#         # FINAL SUCCESS RESULT
#         # ====================================================

#         print()
#         print(
#             "========== FINAL RESULT =========="
#         )


#         print(
#             "Is leaf:",
#             is_leaf
#         )


#         print(
#             "Crop:",
#             crop
#         )


#         print(
#             "Disease:",
#             disease
#         )


#         print(
#             "Confidence:",
#             round(
#                 confidence,
#                 2
#             ),
#             "%"
#         )


#         print(
#             "Severity:",
#             severity
#         )


#         print(
#             "Risk:",
#             risk
#         )


#         print(
#             "=================================="
#         )


#         # ====================================================
#         # IMPORTANT:
#         # is_leaf=True IS SENT HERE
#         # ====================================================

#         return jsonify({

#             "success": True,

#             "status":
#                 "success",

#             "is_leaf":
#                 True,

#             "crop":
#                 crop,

#             "disease":
#                 disease,

#             "confidence":
#                 round(
#                     confidence,
#                     2
#                 ),

#             "severity":
#                 severity,

#             "risk":
#                 risk

#         })


#     # ========================================================
#     # ERROR HANDLING
#     # ========================================================

#     except Exception as error:

#         print()
#         print(
#             "========== ERROR =========="
#         )


#         print(
#             "ERROR:",
#             error
#         )


#         print(
#             "==========================="
#         )


#         return jsonify({

#             "success": False,

#             "is_leaf": False,

#             "message":
#                 "Could not analyze image."

#         }), 500


# # ============================================================
# # START SERVER
# # ============================================================

# if __name__ == "__main__":

#     port = int(
#         os.environ.get(
#             "PORT",
#             5000
#         )
#     )


#     app.run(

#         host="0.0.0.0",

#         port=port,

#         debug=False

#     )


from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import os
import gc
import torch
import numpy as np

from PIL import Image


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)
CORS(app)


# ============================================================
# MEMORY OPTIMIZATION
# ============================================================

# Use fewer CPU threads on small hosting instances.
torch.set_num_threads(1)

try:
    torch.set_num_interop_threads(1)
except Exception:
    pass


# ============================================================
# MODEL
# ============================================================

MODEL_NAME = (
    "linkanjarad/"
    "mobilenet_v2_1.0_224-plant-disease-identification"
)

model = None


def load_model():

    global model

    if model is not None:
        return model

    print()
    print("========================================")
    print("Loading CropGuard AI model...")
    print("========================================")

    from transformers import AutoModelForImageClassification

    model = AutoModelForImageClassification.from_pretrained(
        MODEL_NAME,
        low_cpu_mem_usage=True
    )

    model.eval()

    print("CropGuard AI model loaded! 🌱🤖")
    print("========================================")
    print()

    return model


# ============================================================
# BASE DIRECTORY
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return send_from_directory(
        BASE_DIR,
        "index.html"
    )


# ============================================================
# FRONTEND FILES
# ============================================================

@app.route("/<path:filename>")
def frontend(filename):

    return send_from_directory(
        BASE_DIR,
        filename
    )


# ============================================================
# LIGHTWEIGHT LEAF CHECK
# ============================================================

def check_leaf_image(image):
    """
    Lightweight image check.

    This does NOT use another AI model.
    It uses simple image characteristics to reject
    obvious non-leaf images before disease prediction.
    """

    try:

        # Resize so the calculation is tiny.
        small = image.resize(
            (128, 128)
        )

        arr = np.asarray(
            small
        ).astype(
            np.float32
        )

        # ----------------------------------------------------
        # RGB CHANNELS
        # ----------------------------------------------------

        r = arr[:, :, 0]
        g = arr[:, :, 1]
        b = arr[:, :, 2]

        # ----------------------------------------------------
        # GREEN PIXELS
        # ----------------------------------------------------

        green_pixels = (
            (g > r * 1.05)
            &
            (g > b * 1.03)
            &
            (g > 45)
        )

        green_ratio = float(
            np.mean(green_pixels)
        )

        # ----------------------------------------------------
        # SATURATION
        # ----------------------------------------------------

        max_channel = np.max(
            arr,
            axis=2
        )

        min_channel = np.min(
            arr,
            axis=2
        )

        saturation = (
            max_channel - min_channel
        ) / (
            max_channel + 1.0
        )

        colorful_ratio = float(
            np.mean(
                saturation > 0.15
            )
        )

        # ----------------------------------------------------
        # BRIGHTNESS
        # ----------------------------------------------------

        brightness = float(
            np.mean(arr)
        )

        # ----------------------------------------------------
        # SIMPLE TEXTURE CHECK
        # ----------------------------------------------------

        gray = (
            0.299 * r
            +
            0.587 * g
            +
            0.114 * b
        )

        horizontal_change = np.mean(
            np.abs(
                np.diff(
                    gray,
                    axis=1
                )
            )
        )

        vertical_change = np.mean(
            np.abs(
                np.diff(
                    gray,
                    axis=0
                )
            )
        )

        texture_score = (
            horizontal_change
            +
            vertical_change
        ) / 2.0

        # ----------------------------------------------------
        # LEAF-LIKE SCORE
        # ----------------------------------------------------

        score = 0

        if green_ratio >= 0.08:
            score += 1

        if green_ratio >= 0.18:
            score += 1

        if colorful_ratio >= 0.20:
            score += 1

        if texture_score >= 3.0:
            score += 1

        # ----------------------------------------------------
        # VERY OBVIOUS NON-LEAF IMAGES
        # ----------------------------------------------------

        # Almost completely white / blank image
        if brightness > 245:

            return {
                "is_leaf": False,
                "score": score,
                "green_ratio": green_ratio
            }

        # Very little color and very little green
        if (
            green_ratio < 0.03
            and colorful_ratio < 0.10
        ):

            return {
                "is_leaf": False,
                "score": score,
                "green_ratio": green_ratio
            }

        # ----------------------------------------------------
        # FINAL DECISION
        # ----------------------------------------------------

        is_leaf = (
            score >= 2
            and green_ratio >= 0.08
        )

        return {
            "is_leaf": is_leaf,
            "score": score,
            "green_ratio": green_ratio
        }

    except Exception as error:

        print(
            "Leaf check error:",
            error
        )

        # If the lightweight check fails,
        # don't block the user unnecessarily.
        return {
            "is_leaf": True,
            "score": 0,
            "green_ratio": 0
        }


# ============================================================
# IMAGE PREPARATION
# ============================================================

def prepare_image(image):

    image_array = np.asarray(
        image
    ).astype(
        np.float32
    )

    image_tensor = torch.from_numpy(
        image_array
    )

    image_tensor = image_tensor.permute(
        2,
        0,
        1
    )

    image_tensor = image_tensor.unsqueeze(
        0
    )

    # --------------------------------------------------------
    # RESIZE
    # --------------------------------------------------------

    image_tensor = torch.nn.functional.interpolate(

        image_tensor,

        size=(224, 224),

        mode="bilinear",

        align_corners=False

    )

    # --------------------------------------------------------
    # 0-255 → 0-1
    # --------------------------------------------------------

    image_tensor = (
        image_tensor / 255.0
    )

    # --------------------------------------------------------
    # NORMALIZATION
    # --------------------------------------------------------

    mean = torch.tensor(
        [0.5, 0.5, 0.5],
        dtype=torch.float32
    ).view(
        1,
        3,
        1,
        1
    )

    std = torch.tensor(
        [0.5, 0.5, 0.5],
        dtype=torch.float32
    ).view(
        1,
        3,
        1,
        1
    )

    image_tensor = (
        image_tensor - mean
    ) / std

    return image_tensor


# ============================================================
# VALID CROPS
# ============================================================

VALID_CROPS = [

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


# ============================================================
# CROP NORMALIZATION
# ============================================================

def clean_crop_name(crop):

    crop = str(
        crop
    ).replace(
        "_",
        " "
    )

    crop = crop.replace(
        "  ",
        " "
    ).strip()

    crop_lower = crop.lower()

    # --------------------------------------------------------
    # Standardize maize
    # --------------------------------------------------------

    if (
        "corn" in crop_lower
        or "maize" in crop_lower
    ):

        return "Maize"

    # --------------------------------------------------------
    # Standardize bell pepper
    # --------------------------------------------------------

    if (
        "bell pepper" in crop_lower
        or crop_lower == "pepper"
    ):

        return "Bell Pepper"

    # --------------------------------------------------------
    # Capitalize normal crop names
    # --------------------------------------------------------

    return crop.title()


# ============================================================
# DISEASE CLEANING
# ============================================================

def clean_disease_name(disease):

    disease = str(
        disease
    ).replace(
        "_",
        " "
    )

    disease = disease.replace(
        "  ",
        " "
    ).strip()

    if disease.lower() == "healthy":

        return "No disease detected"

    return disease.title()


# ============================================================
# ANALYZE
# ============================================================

@app.route(
    "/analyze",
    methods=["POST"]
)
def analyze():

    # ========================================================
    # CHECK IMAGE
    # ========================================================

    if "image" not in request.files:

        return jsonify({

            "success": False,

            "message":
                "No image received."

        }), 400


    image_file = request.files[
        "image"
    ]


    if image_file.filename == "":

        return jsonify({

            "success": False,

            "message":
                "No image selected."

        }), 400


    try:

        # ====================================================
        # OPEN IMAGE
        # ====================================================

        image = Image.open(
            image_file
        ).convert(
            "RGB"
        )


        print()
        print("========================================")
        print("NEW IMAGE ANALYSIS")
        print("========================================")


        # ====================================================
        # STEP 1 — LIGHTWEIGHT LEAF CHECK
        # ====================================================

        leaf_check = check_leaf_image(
            image
        )

        is_leaf = leaf_check[
            "is_leaf"
        ]

        print(
            "Green ratio:",
            round(
                leaf_check["green_ratio"] * 100,
                2
            ),
            "%"
        )

        print(
            "Leaf-like score:",
            leaf_check["score"]
        )

        print(
            "Leaf image:",
            is_leaf
        )


        # ====================================================
        # REJECT OBVIOUS NON-LEAF
        # ====================================================

        if not is_leaf:

            print(
                "Image rejected: not a leaf ❌"
            )

            return jsonify({

                "success": True,

                "status": "uncertain",

                "is_leaf": False,

                "management_allowed": False,

                "crop": "Unable to identify",

                "disease": "Not a crop leaf",

                "confidence": 0,

                "severity": "Unknown",

                "risk": "Unknown",

                "message":
                    "Please upload a clear photo of a crop leaf."

            })


        print(
            "Leaf image accepted ✅"
        )


        # ====================================================
        # STEP 2 — LOAD DISEASE MODEL
        # ====================================================

        disease_model = load_model()


        # ====================================================
        # STEP 3 — PREPARE IMAGE
        # ====================================================

        image_tensor = prepare_image(
            image
        )


        # ====================================================
        # STEP 4 — DISEASE PREDICTION
        # ====================================================

        print()
        print(
            "========== DISEASE MODEL =========="
        )


        with torch.inference_mode():

            outputs = disease_model(
                pixel_values=image_tensor
            )


        # ====================================================
        # PROBABILITIES
        # ====================================================

        probabilities = torch.softmax(
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


        predicted_class = int(
            predicted_class.item()
        )


        confidence = float(
            confidence.item() * 100
        )


        # ====================================================
        # GET LABEL
        # ====================================================

        label = disease_model.config.id2label.get(
            predicted_class,
            "Unknown"
        )


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
        # PARSE LABEL
        # ====================================================

        raw_label = str(
            label
        ).strip()


        if "___" in raw_label:

            parts = raw_label.split(
                "___",
                1
            )

            crop = parts[0].strip()

            disease = parts[1].strip()


        elif " with " in raw_label:

            parts = raw_label.split(
                " with ",
                1
            )

            crop = parts[0].strip()

            disease = parts[1].strip()


        elif raw_label.lower().startswith(
            "healthy "
        ):

            crop = raw_label[
                len("Healthy "):
            ].strip()

            disease = "No disease detected"


        else:

            crop = raw_label.strip()

            disease = "Unknown"


        # ====================================================
        # CLEAN NAMES
        # ====================================================

        crop = clean_crop_name(
            crop
        )

        disease = clean_disease_name(
            disease
        )


        # ====================================================
        # HEALTHY CHECK
        # ====================================================

        disease_lower = disease.lower()

        is_healthy = (

            "healthy" in disease_lower

            or

            "no disease" in disease_lower

        )


        if is_healthy:

            disease = "No disease detected"


        # ====================================================
        # VALID CROP CHECK
        # ====================================================

        crop_lower = crop.lower()

        is_valid_crop = any(

            valid_crop in crop_lower

            for valid_crop in VALID_CROPS

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
        # LOW CONFIDENCE
        # ====================================================

        if confidence < 80:

            print(
                "Prediction confidence too low ❌"
            )

            return jsonify({

                "success": True,

                "status": "uncertain",

                "is_leaf": True,

                "management_allowed": False,

                "crop": "Unable to identify",

                "disease": "Uncertain result",

                "confidence": round(
                    confidence,
                    2
                ),

                "severity": "Unknown",

                "risk": "Unknown",

                "message":
                    "CropGuard could not confidently identify this leaf."

            })


        # ====================================================
        # INVALID CROP
        # ====================================================

        if not is_valid_crop:

            print(
                "Unsupported crop ❌"
            )

            return jsonify({

                "success": True,

                "status": "uncertain",

                "is_leaf": True,

                "management_allowed": False,

                "crop": "Unable to identify",

                "disease": "Uncertain result",

                "confidence": round(
                    confidence,
                    2
                ),

                "severity": "Unknown",

                "risk": "Unknown",

                "message":
                    "CropGuard could not identify a supported crop leaf."

            })


        # ====================================================
        # SEVERITY + RISK
        # ====================================================

        if is_healthy:

            severity = "None"

            risk = "Healthy"


        elif confidence >= 90:

            severity = "Moderate"

            risk = "High Risk"


        else:

            severity = "Moderate"

            risk = "Medium Risk"


        # ====================================================
        # MANAGEMENT ALLOWED
        # ====================================================

        management_allowed = True


        # ====================================================
        # FINAL RESULT
        # ====================================================

        print()
        print(
            "========== FINAL RESULT =========="
        )

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
            "Management:",
            "Allowed"
        )

        print(
            "=================================="
        )


        # ====================================================
        # CLEAN TEMP MEMORY
        # ====================================================

        del image_tensor
        del outputs
        del probabilities

        gc.collect()


        # ====================================================
        # RESPONSE
        # ====================================================

        return jsonify({

            "success": True,

            "status": "success",

            "is_leaf": True,

            "management_allowed":
                management_allowed,

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
    # ERROR
    # ========================================================

    except Exception as error:

        print()
        print(
            "========== ERROR =========="
        )

        print(
            "ERROR:",
            error
        )

        print(
            "==========================="
        )

        gc.collect()


        return jsonify({

            "success": False,

            "message":
                "Could not analyze image."

        }), 500


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route(
    "/health",
    methods=["GET"]
)
def health():

    return jsonify({

        "status": "ok",

        "service":
            "CropGuard"

    })


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(

        host="0.0.0.0",

        port=port,

        debug=False

    )