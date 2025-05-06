from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
from PIL import Image
import torch
from pipeline_final import Final_model
import io
import os
app = FastAPI()

model_path = "C:/Users/aslam/OneDrive/Documents/Finalyearproject/pix2pix/deployment/finalyearmodel"
device = "cuda" if torch.cuda.is_available() else "cpu"
pipe = Final_model.from_pretrained(model_path).to(device)

output_dir = "outputs"
os.makedirs(output_dir, exist_ok=True)

@app.post("/edit-image/")
async def edit_image(file: UploadFile = File(...), prompt: str = Form(...)):
    image = Image.open(io.BytesIO(await file.read())).convert("RGB")
    edited_image = pipe(image=image, prompt=prompt, guidance_scale=12, num_inference_steps=50).images[0]
    output_path = f"{output_dir}/edited_{file.filename}"
    edited_image.save(output_path)

    return FileResponse(output_path, media_type="image/png", filename=f"edited_{file.filename}")

@app.get("/")
def home():
    return {"message": "Welcome to FinalYearModel FastAPI!"}
