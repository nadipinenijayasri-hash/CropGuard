from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import torch

MODEL_NAME = "openai/clip-vit-base-patch32"

print("Loading CLIP...")

processor = CLIPProcessor.from_pretrained(MODEL_NAME)
model = CLIPModel.from_pretrained(MODEL_NAME)

model.eval()

print("CLIP ready!")


# CHANGE THIS PATH TO YOUR PARROT IMAGE
image = Image.open("../test_image.png").convert("RGB")


labels = [
    "a crop leaf",
    "a plant",
    "a leaf",
    "an animal",
    "a bird",
    "a person",
    "a building",
    "a random object"
]


inputs = processor(
    text=labels,
    images=image,
    return_tensors="pt",
    padding=True
)


with torch.no_grad():

    outputs = model(**inputs)

    probabilities = outputs.logits_per_image.softmax(
        dim=1
    )[0]


print("\nCLIP RESULTS:\n")

for label, probability in zip(labels, probabilities):

    print(
        f"{label}: {probability.item() * 100:.2f}%"
    )


best_index = probabilities.argmax().item()

print("\nBEST MATCH:")
print(labels[best_index])