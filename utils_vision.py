import fitz  # PyMuPDF
from PIL import Image, ImageDraw
import io
import base64
import json
import os
from openai import OpenAI
from utils_database import get_ai_memory_context

# Initialize Client safely
try:
    client = OpenAI()
except:
    client = None

def pdf_page_to_image(uploaded_file):
    """Converts the first page of a PDF file object to a PIL Image."""
    try:
        uploaded_file.seek(0)
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        page = doc.load_page(0)
        pix = page.get_pixmap(dpi=150) # Lower DPI for UI responsiveness
        img = Image.open(io.BytesIO(pix.tobytes()))
        return img
    except Exception as e:
        print(f"Error converting PDF: {e}")
        return None

def encode_image(image):
    buffered = io.BytesIO()
    image.convert("RGB").save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def detect_clashes_with_boxes(overlay_image, scale_context, trade_a, trade_b):
    """
    Analyzes the image for clashes using GPT-4o and draws boxes around them.
    """
    base64_image = encode_image(overlay_image)
    
    # 1. RETRIEVE MEMORY
    memory_context = get_ai_memory_context()
    
    rules = "Identify physical overlaps that are impossible or costly."
    if "Structural" in trade_a or "Structural" in trade_b:
        rules += " CRITICAL: Nothing can penetrate Structural Columns or Beams."
        
    prompt = f"""
    Act as a Lead Coordinator.
    Context: '{trade_a}' vs '{trade_b}'. Scale: {scale_context}.
    Task: {rules}
    
    {memory_context}
    
    Return JSON with key 'clashes'. 
    Item format: {{ "description": "Specific issue description", "box_2d": [ymin, xmin, ymax, xmax] }} 
    Coordinates must be 0-1000 scale.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={ "type": "json_object" },
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}]}
            ],
            max_tokens=600
        )
        
        content = response.choices[0].message.content
        data = json.loads(content)
        clashes = data.get("clashes", [])
        
        # Draw the boxes
        draw = ImageDraw.Draw(overlay_image)
        width, height = overlay_image.size
        
        for clash in clashes:
            ymin, xmin, ymax, xmax = clash['box_2d']
            box = [xmin * width / 1000, ymin * height / 1000, xmax * width / 1000, ymax * height / 1000]
            draw.rectangle(box, outline="red", width=5)
            
        return overlay_image, clashes
            
    except Exception as e:
        print(f"AI Error: {e}")
        return overlay_image, [{"description": f"AI Analysis Failed: {e}"}]

# Helper functions for transformations (if needed by app.py imports in future, kept for safety)
def normalize_images(img1, img2):
    if img1.size != img2.size:
        return img1, img2.resize(img1.size, Image.Resampling.LANCZOS)
    return img1, img2

def transform_image(img, x_shift, y_shift, rotation):
    if rotation != 0:
        img = img.rotate(rotation, resample=Image.BICUBIC, expand=False)
    return img.transform(img.size, Image.AFFINE, (1, 0, -x_shift, 0, 1, -y_shift), resample=Image.BICUBIC)

def create_overlay(img1, img2, opacity=0.5):
    img1 = img1.convert("RGBA")
    img2 = img2.convert("RGBA")
    return Image.blend(img1, img2, alpha=opacity)