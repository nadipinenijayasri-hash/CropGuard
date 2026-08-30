import torch
from PIL import Image
from torchvision import transforms
from transformers import AutoModelForImageClassification

MODEL_NAME = "linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification"

IMAGE_PATH = r"C:\Users\nadip\Desktop\CropGuard\test_image.png"

print("Loading AI model...")

model = AutoModelForImageClassification.from_pretrained(MODEL_NAME)
model.eval()

print("Model loaded! 🌱")


# Image preprocessing
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.5, 0.5, 0.5],
        std=[0.5, 0.5, 0.5]
    )
])


print("Loading image...")

image = Image.open(IMAGE_PATH).convert("RGB")

image_tensor = transform(image).unsqueeze(0)


print("Running prediction...")

with torch.no_grad():
    outputs = model(pixel_values=image_tensor)

probabilities = torch.nn.functional.softmax(
    outputs.logits,
    dim=1
)

top_probabilities, top_classes = torch.topk(
    probabilities,
    5
)

print("\n==============================")
print("🌱 CROP GUARD TOP 5 RESULTS")
print("==============================")

for probability, class_id in zip(
    top_probabilities[0],
    top_classes[0]
):
    label = model.config.id2label[class_id.item()]
    confidence = probability.item() * 100

    print(
        f"{label} → {confidence:.2f}%"
    )

print("==============================")