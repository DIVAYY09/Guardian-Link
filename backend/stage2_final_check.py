
import os
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.ai.vision.imageanalysis.aio import ImageAnalysisClient
from azure.cognitiveservices.vision.customvision.prediction import CustomVisionPredictionClient
from msrest.authentication import ApiKeyCredentials

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_audit():
    print("--- Stage 2 Final Audit ---")
    
    # 1. Environment Loading
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
    
    vision_key = os.getenv("AZURE_VISION_KEY")
    vision_endpoint = os.getenv("AZURE_VISION_ENDPOINT")
    cv_key = os.getenv("AZURE_CUSTOM_VISION_KEY")
    cv_endpoint = os.getenv("AZURE_CUSTOM_VISION_ENDPOINT")
    cv_project_id = os.getenv("AZURE_CUSTOM_VISION_PROJECT_ID")
    cv_iteration = os.getenv("AZURE_CUSTOM_VISION_ITERATION_NAME")
    
    # 2. Environment Validation
    missing = []
    if not vision_key: missing.append("AZURE_VISION_KEY")
    if not vision_endpoint: missing.append("AZURE_VISION_ENDPOINT")
    if not cv_key: missing.append("AZURE_CUSTOM_VISION_KEY")
    
    if missing:
        print(f"[FAIL] Missing Environment Variables: {', '.join(missing)}")
        return
    else:
        print("[PASS] Environment Variables Present.")

    # 3. Temporal Logic Check (Static Analysis of imported main)
    try:
        from main import FRAME_HISTORY
        from collections import deque
        if isinstance(FRAME_HISTORY, deque) and FRAME_HISTORY.maxlen > 1:
            print(f"[PASS] Temporal Logic Found: FRAME_HISTORY (maxlen={FRAME_HISTORY.maxlen})")
        else:
            print("[FAIL] Temporal Logic: FRAME_HISTORY not found or invalid.")
    except ImportError:
        # We might need to add parent dir to path to import main
        import sys
        sys.path.append(str(Path(__file__).parent))
        try:
            from main import FRAME_HISTORY
            print(f"[PASS] Temporal Logic Found: FRAME_HISTORY (maxlen={FRAME_HISTORY.maxlen})")
        except:
            print("[FAIL] Temporal Logic: Could not import main.FRAME_HISTORY")

    # 4. Live Handshake
    print("\n--- Live Service Handshake ---")
    
    success_cv = False
    success_vision = False
    
    # Custom Vision
    try:
        credentials = ApiKeyCredentials(in_headers={"Prediction-Key": cv_key})
        cv_client = CustomVisionPredictionClient(endpoint=cv_endpoint, credentials=credentials)
        import base64
        # Valid 1x1 white pixel JPEG
        dummy_b64 = "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD3+iiigD//2Q=="
        dummy_image = base64.b64decode(dummy_b64)
        
        cv_client.classify_image(cv_project_id, cv_iteration, dummy_image)
        print("[PASS] Custom Vision handshake successful.")
        success_cv = True
    except Exception as e:
        print(f"[FAIL] Custom Vision handshake failed: {e}")

    # Azure Vision
    try:
        async with ImageAnalysisClient(
            endpoint=vision_endpoint,
            credential=AzureKeyCredential(vision_key)
        ) as client:
            result = await client.analyze(
                image_data=dummy_image,
                visual_features=[
                    "Objects" 
                ]
            )
            print(f"[PASS] Azure Vision handshake successful.")
            success_vision = True
    except Exception as e:
        print(f"[FAIL] Azure Vision handshake failed: {e}")

    print("\n--- Final Status ---")
    if success_cv and success_vision:
        print("SUCCESS")
    else:
        print("AUDIT FAILED")

if __name__ == "__main__":
    asyncio.run(run_audit())
