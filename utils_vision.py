# ... (keep existing imports)
from utils_database import get_ai_memory_context # Import the new memory tool

# ... (keep other functions like pdf_page_to_image, etc.)

def detect_clashes_with_boxes(overlay_image, scale_context, trade_a, trade_b):
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
    
    {memory_context}  <-- THIS IS THE AI LEARNING FROM PAST USER FEEDBACK
    
    Return JSON with key 'clashes'. 
    Item format: {{ "description": "Specific issue description", "box_2d": [ymin, xmin, ymax, xmax] }} 
    """
    
    # ... (Rest of the function remains exactly the same)
    # Just ensure you use the updated 'prompt' variable in the API call
    response = client.chat.completions.create(
        model="gpt-4o",
        response_format={ "type": "json_object" },
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}]}
        ],
        max_tokens=600
    )
    # ... (Keep the parsing logic)
    try:
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
    except Exception as e:
        return overlay_image, []