import fitz
from PIL import Image, ImageDraw
import io
import base64
import json
import os
from openai import OpenAI
from fpdf import FPDF

# Initialize Client safely
try:
    client = OpenAI()
except:
    client = None

def pdf_page_to_image(uploaded_file):
    uploaded_file.seek(0)
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    page = doc.load_page(0)
    pix = page.get_pixmap(dpi=150) # Lower DPI for UI responsiveness
    img = Image.open(io.BytesIO(pix.tobytes()))
    return img

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

def encode_image(image):
    buffered = io.BytesIO()
    image.convert("RGB").save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def extract_scale_from_image(image):
    width, height = image.size
    bottom_crop = image.crop((0, int(height * 0.8), width, height))
    base64_image = encode_image(bottom_crop)

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": "Read the architectural scale. Return ONLY text (e.g. 1/8\" = 1'-0\"). If not found, return 'Unknown'."
                },
                {
                    "role": "user",
                    "content": [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}]
                }
            ],
            max_tokens=50
        )
        return response.choices[0].message.content
    except:
        return "Unknown"

def detect_clashes_with_boxes(overlay_image, scale_context, trade_a, trade_b):
    base64_image = encode_image(overlay_image)

    rules = "Identify physical overlaps that are impossible or costly."
    if "Structural" in trade_a or "Structural" in trade_b:
        rules += " CRITICAL: Nothing can penetrate Structural Columns or Beams."

    prompt = f"""
    Act as a Lead Coordinator. Context: '{trade_a}' vs '{trade_b}'. Scale: {scale_context}.
    Task: {rules}. Return JSON with key 'clashes'. 
    Item format: {{ "description": "text", "box_2d": [ymin, xmin, ymax, xmax] }} (0-1000 scale).
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

        draw = ImageDraw.Draw(overlay_image)
        width, height = overlay_image.size

        for clash in clashes:
            ymin, xmin, ymax, xmax = clash['box_2d']
            box = [xmin * width / 1000, ymin * height / 1000, xmax * width / 1000, ymax * height / 1000]
            draw.rectangle(box, outline="red", width=5)

        return overlay_image, clashes
    except:
        return overlay_image, []

def create_pdf_report(annotated_img, clashes):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=16)
    pdf.cell(200, 10, txt="Tectonica Clash Report", ln=1, align="C")

    temp_path = "temp_report_img.jpg"
    annotated_img.convert("RGB").save(temp_path)
    pdf.image(temp_path, x=10, y=30, w=190)

    if os.path.exists(temp_path):
        os.remove(temp_path)

    return pdf.output(dest='S').encode('latin-1')