from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import torch
from diffusers import StableDiffusionInstructPix2PixPipeline
from PIL import Image, ImageFilter
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
import os
import uuid
import time
from pydantic import BaseModel
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ReDEFINE API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


UPLOAD_DIR = "uploads"
OUTPUT_DIR = "results"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/results", StaticFiles(directory=OUTPUT_DIR), name="results")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

progress_store = {}

# Load model
device = "cuda" if torch.cuda.is_available() else "cpu"
logger.info(f"Running on: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")

model_path = "C:/Users/thali/Projects/deployment/finalyearmodel"  # Update this to your model path
pipe = None

# Lazy load model to save memory on startup
def load_model():
    global pipe
    if pipe is None:
        logger.info("Loading model...")
        pipe = StableDiffusionInstructPix2PixPipeline.from_pretrained(model_path).to(device)
        logger.info("✅ Model loaded successfully!")
    return pipe

# Helper functions
def preprocess_image(image_path):
    image = Image.open(image_path).convert("RGB")
    image = image.resize((512, 512))
    return image

def enhance_output(image):
    image = image.filter(ImageFilter.SHARPEN)
    image = image.filter(ImageFilter.SMOOTH_MORE)
    return image

def compute_metrics(original, edited):
    original = np.array(original)
    edited = np.array(edited)
    
    # Resize if dimensions don't match
    if original.shape[:2] != edited.shape[:2]:
        edited = cv2.resize(edited, (original.shape[1], original.shape[0]))
    
    # Calculate SSIM
    original_gray = cv2.cvtColor(original, cv2.COLOR_RGB2GRAY)
    edited_gray = cv2.cvtColor(edited, cv2.COLOR_RGB2GRAY)
    ssim_score = ssim(original_gray, edited_gray)
    
    # Calculate PSNR
    mse = np.mean((original - edited) ** 2)
    if mse == 0:
        psnr = 100
    else:
        max_pixel = 255.0
        psnr = 20 * np.log10(max_pixel / np.sqrt(mse))
    
    return {"ssim": float(ssim_score), "psnr": float(psnr)}

# Process image in background
def process_image(task_id, image_path, instruction, guidance_scale, num_inference_steps):
    try:
        # Update progress
        progress_store[task_id] = {"status": "processing", "progress": 0}
        
        # Load model
        model = load_model()
        progress_store[task_id]["progress"] = 10
        
        # Preprocess image
        original_image = preprocess_image(image_path)
        progress_store[task_id]["progress"] = 20
        
        # Generate image
        def callback_fn(i, t, latents):
            # Calculate progress based on steps
            progress = int(20 + (i / num_inference_steps) * 60)
            progress_store[task_id]["progress"] = min(80, progress)
            return {"progress": progress}
        
        # Run model inference
        edited_image = model(
            image=original_image,
            prompt=instruction,
            guidance_scale=guidance_scale,
            num_inference_steps=num_inference_steps,
            callback=callback_fn,
            callback_steps=1
        ).images[0]
        
        progress_store[task_id]["progress"] = 80
        
        # Enhance output
        enhanced_image = enhance_output(edited_image)
        progress_store[task_id]["progress"] = 90
        
        # Compute metrics
        metrics = compute_metrics(original_image, enhanced_image)
        
        # Save output
        output_filename = f"{task_id}.png"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        enhanced_image.save(output_path)
        
        # Update progress store with results
        progress_store[task_id] = {
            "status": "completed",
            "progress": 100,
            "output_path": f"/results/{output_filename}",
            "metrics": metrics
        }
        
        logger.info(f"✅ Task {task_id} completed successfully!")
        
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        progress_store[task_id] = {"status": "error", "error": str(e), "progress": 0}

# API endpoints
@app.get("/")
async def get_root():
    return FileResponse("static/index.html")

@app.post("/upload/")
async def upload_image(file: UploadFile = File(...)):
    try:
        # Generate unique ID for the file
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}{file_extension}")
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        
        return {"status": "success", "file_id": file_id, "file_path": f"/uploads/{file_id}{file_extension}"}
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@app.post("/generate/")
async def generate_image(
    background_tasks: BackgroundTasks,
    file_path: str = Form(...),
    instruction: str = Form(...),
    guidance_scale: float = Form(12.0),
    num_inference_steps: int = Form(50)
):
    try:
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Get full file path
        if file_path.startswith("/uploads/"):
            file_path = os.path.join(UPLOAD_DIR, file_path.split("/uploads/")[1])
        
        # Start processing in background
        background_tasks.add_task(
            process_image,
            task_id,
            file_path,
            instruction,
            guidance_scale,
            num_inference_steps
        )
        
        return {"status": "processing", "task_id": task_id}
    except Exception as e:
        logger.error(f"Error starting generation: {str(e)}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@app.get("/progress/{task_id}")
async def get_progress(task_id: str):
    if task_id in progress_store:
        return progress_store[task_id]
    return {"status": "not_found"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "device": device}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
