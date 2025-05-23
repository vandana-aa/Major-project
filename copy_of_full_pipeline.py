# -*- coding: utf-8 -*-
"""Copy of full_pipeline.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1QHNjfqOdAQgUXxOtZJ6YO7a5UXGas-Bs
"""

from google.colab import drive
drive.mount("/content/drive")

from google.colab import files
uploaded = files.upload()  # Upload a breast image

# Step 2: Load U-Net Keras model and segment the image
from keras.models import load_model
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt

# Load U-Net model
unet_model = load_model('/content/drive/MyDrive/unet_model.h5', compile=False)

# Load uploaded image
img_path = list(uploaded.keys())[0]
img = Image.open(img_path).convert('RGB').resize((256, 256))

# Convert to normalized numpy array
img_np = np.array(img) / 255.0  # Shape: (256, 256, 3)
img_input = np.expand_dims(img_np, axis=0)  # Shape: (1, 256, 256, 3)

# Predict segmentation mask
pred_mask = unet_model.predict(img_input)[0, :, :, 0]  # Output shape: (256, 256)
binary_mask = (pred_mask > 0.5).astype(np.uint8)

# Visualize the mask
plt.imshow(binary_mask, cmap='gray')
plt.title("Segmentation Mask")
plt.axis('off')
plt.show()

# Step 3: Apply the mask to the original image for classification
masked_img_np = img_np * binary_mask[..., np.newaxis]  # Shape: (256, 256, 3)

plt.imshow(masked_img_np)
plt.title("Masked ROI Image")
plt.axis('off')
plt.show()

# Split the masked image vertically into left and right halves
height, width, _ = masked_img_np.shape
midpoint = width // 2

left_half = masked_img_np[:, :midpoint, :]
right_half = masked_img_np[:, midpoint:, :]

# Show both halves
fig, axs = plt.subplots(1, 2, figsize=(10, 5))
axs[0].imshow(left_half)
axs[0].set_title("Left Breast")
axs[0].axis('off')

axs[1].imshow(right_half)
axs[1].set_title("Right Breast")
axs[1].axis('off')

plt.show()

import timm
import torch
from torchvision import transforms
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

# DEVICE
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# === Load Swin Transformer === #
def load_swin_classifier():
    model = timm.create_model("convnext_tiny.fb_in22k", pretrained=False, num_classes=2)
    model.load_state_dict(torch.load('/content/drive/MyDrive/convnext_tiny.fb_in22k_vmodel.pth', map_location=DEVICE))
    model.to(DEVICE)
    model.eval()
    return model

swin_model = load_swin_classifier()

# === Transform (must match training) === #
transform = transforms.Compose([
    transforms.ToPILImage(),  # Convert from ndarray to PIL before resizing
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
])

# === Prediction Function === #
def predict_and_show(img_np_half, label=''):
    img_uint8 = (img_np_half * 255).astype(np.uint8)

    # Prepare tensor for model
    img_tensor = transform(img_uint8).unsqueeze(0).to(DEVICE)

    # Predict
    with torch.no_grad():
        output = swin_model(img_tensor)
        prediction = torch.argmax(output, dim=1).item()

    label_str = "Benign" if prediction == 0 else "Malignant"

    # Show image with label
    plt.imshow(img_uint8)
    plt.title(f"{label} - {label_str}")
    plt.axis('off')
    plt.show()

    return label_str

# === Predict and Show Images === #
predict_and_show(left_half, "Left Breast")
predict_and_show(right_half, "Right Breast")

