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

torch.set_num_threads(1)

try:
    torch.set_num_interop_threads(1)
except Exception:
    pass


# ============================================================
# MODEL — CROP DISEASE MODEL
# ============================================================

MODEL_NAME = (
    "linkanjarad/"
    "mobilenet_v2_1.0_224-plant-disease-identification"
)

print()
print("==========================================")
print("Loading CropGuard AI model...")
print("==========================================")


from transformers import AutoModelForImageClassification


model = AutoModelForImageClassification.from_pretrained(
    MODEL_NAME
)

model.eval()

print("CropGuard AI model loaded! 🌱🤖")


# ============================================================
# SUPPORTED CROPS
# ============================================================

SUPPORTED_CROPS = [

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
# CLEAN CROP NAME
# ============================================================

def clean_crop_name(crop):

    crop = str(crop)

    crop = crop.replace(
        "_",
        " "
    )

    crop = crop.replace(
        "(",
        ""
    )

    crop = crop.replace(
        ")",
        ""
    )

    crop = crop.replace(
        "  ",
        " "
    )

    crop = crop.strip()


    # Normalize corn / maize

    if "corn" in crop.lower():

        return "Maize"


    if "maize" in crop.lower():

        return "Maize"


    return crop


# ============================================================
# CHECK SUPPORTED CROP
# ============================================================

def is_supported_crop(crop):

    crop_lower = crop.lower()

    for supported in SUPPORTED_CROPS:

        if supported in crop_lower:

            return True

    return False


# ============================================================
# LIGHTWEIGHT IMAGE CHECK
# ============================================================
#
# IMPORTANT:
#
# We removed CLIP because it was causing Render
# to run out of RAM and exit with status 137.
#
# This is NOT an AI leaf classifier.
#
# It is only a lightweight sanity check used to
# reject obviously non-plant images.
#
# ============================================================

def basic_leaf_check(image):

    try:

        # Resize small to reduce memory

        small = image.copy()

        small.thumbnail(
            (256, 256)
        )


        image_array = np.asarray(
            small
        ).astype(
            np.float32
        )


        if image_array.size == 0:

            return False, 0


        r = image_array[:, :, 0]

        g = image_array[:, :, 1]

        b = image_array[:, :, 2]


        # Green vegetation pixels

        green_mask = (

            (g > r * 1.05)

            &

            (g > b * 1.05)

            &

            (g > 45)

        )


        green_ratio = (
            green_mask.mean()
        )


        # Yellow / brown vegetation pixels
        #
        # Useful for diseased leaves that are not
        # strongly green.

        yellow_brown_mask = (

            (r > 55)

            &

            (g > 45)

            &

            (r > b * 1.15)

            &

            (g > b * 1.10)

        )


        yellow_brown_ratio = (
            yellow_brown_mask.mean()
        )


        vegetation_ratio = (

            green_ratio

            +

            yellow_brown_ratio * 0.35

        )


        score = min(
            vegetation_ratio,
            1.0
        )


        # Very basic sanity threshold.
        #
        # This mainly rejects obvious photos such as
        # people, screens, buildings, random objects etc.
        #
        # Disease model + supported crop check are still
        # used for the actual prediction.

        looks_like_vegetation = (

            score >= 0.12

        )


        return (
            looks_like_vegetation,
            score
        )


    except Exception as error:

        print(
            "Leaf check error:",
            error
        )

        # Do not crash the analysis

        return True, 0.0


# ============================================================
# ANALYZE IMAGE
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

            "is_leaf": False,

            "message":
                "No image received."

        }), 400


    image_file = request.files["image"]


    if image_file.filename == "":

        return jsonify({

            "success": False,

            "is_leaf": False,

            "message":
                "No image selected."

        }), 400


    try:


        # ====================================================
        # OPEN IMAGE
        # ====================================================

        image = Image.open(
            image_file
        ).convert("RGB")


        # ====================================================
        # BASIC LEAF / VEGETATION CHECK
        # ====================================================

        print()
        print(
            "========== IMAGE CHECK =========="
        )


        looks_like_leaf, vegetation_score = (
            basic_leaf_check(image)
        )


        print(
            "Vegetation score:",
            round(
                vegetation_score * 100,
                2
            ),
            "%"
        )


        # ====================================================
        # REJECT OBVIOUS NON-PLANT IMAGE
        # ====================================================

        if not looks_like_leaf:

            print(
                "Image rejected: Not a likely leaf image ❌"
            )


            return jsonify({

                "success": True,

                "status": "invalid",

                "is_leaf": False,

                "crop":
                    "Unable to identify",

                "disease":
                    "Not a crop leaf",

                "confidence":
                    round(
                        vegetation_score * 100,
                        2
                    ),

                "severity":
                    "Unknown",

                "risk":
                    "Unknown",

                "message":
                    "Please upload a clear crop leaf image."

            })


        print(
            "Image passed basic vegetation check ✅"
        )


        # ====================================================
        # PREPARE IMAGE
        # ====================================================

        image_array = np.array(
            image
        )


        image_tensor = torch.from_numpy(
            image_array
        ).permute(
            2,
            0,
            1
        ).unsqueeze(
            0
        ).float()


        # ====================================================
        # RESIZE
        # ====================================================

        image_tensor = torch.nn.functional.interpolate(

            image_tensor,

            size=(224, 224),

            mode="bilinear",

            align_corners=False

        )


        # ====================================================
        # NORMALIZE 0-255 → 0-1
        # ====================================================

        image_tensor = (
            image_tensor / 255.0
        )


        # ====================================================
        # NORMALIZATION
        # ====================================================

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


        # ====================================================
        # DISEASE MODEL
        # ====================================================

        print()
        print(
            "========== DISEASE MODEL =========="
        )


        with torch.inference_mode():

            outputs = model(
                pixel_values=image_tensor
            )


        # ====================================================
        # PROBABILITIES
        # ====================================================

        disease_probabilities = torch.softmax(

            outputs.logits,

            dim=1

        )


        # ====================================================
        # BEST PREDICTION
        # ====================================================

        confidence, predicted_class = torch.max(

            disease_probabilities,

            dim=1

        )


        predicted_class = (
            predicted_class.item()
        )


        confidence = (
            confidence.item() * 100
        )


        # ====================================================
        # GET MODEL LABEL
        # ====================================================

        label = model.config.id2label[
            predicted_class
        ]


        raw_label = str(
            label
        ).strip()


        print(
            "RAW MODEL LABEL:",
            raw_label
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

        crop = ""

        disease = ""


        # ----------------------------------------------------
        # PlantVillage format
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
        # "with" format
        # ----------------------------------------------------

        elif " with " in raw_label:

            parts = raw_label.split(
                " with ",
                1
            )


            crop = parts[0].strip()

            disease = parts[1].strip()


        # ----------------------------------------------------
        # Healthy format
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


        # ----------------------------------------------------
        # Unknown format
        # ----------------------------------------------------

        else:

            crop = raw_label.strip()

            disease = "Unknown"


        # ====================================================
        # CLEAN CROP
        # ====================================================

        crop = clean_crop_name(
            crop
        )


        # ====================================================
        # CLEAN DISEASE
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

        disease_lower = (
            disease.lower()
        )


        if (

            "healthy" in disease_lower

            or

            "no disease" in disease_lower

        ):

            disease = (
                "No disease detected"
            )


        # ====================================================
        # SUPPORTED CROP CHECK
        # ====================================================

        supported = is_supported_crop(
            crop
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
            "Supported crop:",
            supported
        )


        # ====================================================
        # UNSUPPORTED CROP
        # ====================================================

        if not supported:

            print(
                "Crop unsupported ⚠️"
            )


            return jsonify({

                "success": True,

                "status":
                    "unsupported",

                "is_leaf":
                    True,

                "crop":
                    crop
                    if crop
                    else
                    "Leaf detected",

                "disease":
                    "Crop not supported",

                "confidence":
                    round(
                        confidence,
                        2
                    ),

                "severity":
                    "Unknown",

                "risk":
                    "Unknown",

                "message":
                    "A leaf was detected, but this crop is not currently supported by CropGuard."

            })


        # ====================================================
        # LOW CONFIDENCE
        # ====================================================

        if confidence < 80:

            print(
                "Disease confidence too low ❌"
            )


            return jsonify({

                "success": True,

                "status":
                    "uncertain",

                "is_leaf":
                    True,

                "crop":
                    crop,

                "disease":
                    "Uncertain result",

                "confidence":
                    round(
                        confidence,
                        2
                    ),

                "severity":
                    "Unknown",

                "risk":
                    "Unknown",

                "message":
                    "CropGuard could not confidently identify the condition."

            })


        # ====================================================
        # SEVERITY + RISK
        # ====================================================

        if disease == "No disease detected":

            severity = "None"

            risk = "Healthy"


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
        print(
            "========== FINAL RESULT =========="
        )


        print(
            "Is leaf:",
            True
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
            "=================================="
        )


        # ====================================================
        # CLEAN MEMORY AFTER PREDICTION
        # ====================================================

        del image_array

        del image_tensor

        del outputs

        del disease_probabilities

        gc.collect()


        # ====================================================
        # RETURN RESULT
        # ====================================================

        return jsonify({

            "success": True,

            "status":
                "success",

            "is_leaf":
                True,

            "crop":
                crop,

            "disease":
                disease,

            "confidence":
                round(
                    confidence,
                    2
                ),

            "severity":
                severity,

            "risk":
                risk

        })


    # ========================================================
    # ERROR HANDLING
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

            "is_leaf": False,

            "message":
                "Could not analyze image."

        }), 500


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