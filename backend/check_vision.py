"""Use a generated test label to verify Gemini vision without customer images."""
import io
import json
from PIL import Image, ImageDraw
from rag.multimodal import GeminiMultimodal

image = Image.new('RGB', (600, 180), 'white')
ImageDraw.Draw(image).text((30, 55), 'TEST DEVICE P001', fill='black', font_size=38)
buffer = io.BytesIO()
image.save(buffer, format='PNG')
try:
    answer = GeminiMultimodal().describe_image_bytes(buffer.getvalue(), 'image/png', 'Read the label. Return only its text.')
    print(json.dumps({'vision': 'ok' if 'P001' in answer else 'unverified', 'label_found': 'P001' in answer}))
except Exception as exc:
    print(json.dumps({'vision':'failed','error_type':type(exc).__name__,'code':getattr(exc,'code',None)}))
    raise SystemExit(1)
