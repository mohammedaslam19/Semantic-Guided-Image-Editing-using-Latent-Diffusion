# Semantic-Guided-Image-Editing-using-Latent-Diffusion

An AI-powered image editing application that transforms existing images based on natural language instructions. This project combines CLIP-based text and vision encoders with a fine-tuned Latent Diffusion Model (LDM) and U-Net architecture to apply precise, high-quality modifications while preserving image structure.

Key Features
Text-Guided Editing: Edit images using simple text prompts like "make the sky more vibrant".

CLIP Conditioning: Encodes both image and instruction to guide transformations semantically.

Latent Diffusion Model: Efficiently performs editing in latent space for better speed and quality.

Cross-Attention Mechanism: Injects textual context into U-Net layers for accurate conditioning.

Modular Architecture: Clean separation of feature extraction, editing pipeline, and UI.

Deployment-Ready: FastAPI-based backend ready for integration with custom frontend.

**Output Image**
Given Input Image :
![image](https://github.com/user-attachments/assets/50a8e8ba-ad8a-4251-a098-6817a90df76a)

Edited Image :
![image](https://github.com/user-attachments/assets/c003534a-678e-4eb9-a231-173c85f6c5b7)

