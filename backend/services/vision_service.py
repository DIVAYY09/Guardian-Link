import os
import logging
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# --- FORCE LOAD .ENV ---
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path, override=True)
# -----------------------

from azure.ai.vision.imageanalysis.aio import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AzureVisionClient:
    """
    MVP VERSION: Uses 'Person Detection' to simulate 'Gesture Detection'.
    """
    def __init__(self):
        self.endpoint = os.getenv("AZURE_VISION_ENDPOINT")
        self.key = os.getenv("AZURE_VISION_KEY")

        if not self.endpoint or not self.key:
            logger.warning("Azure Vision credentials missing.")
            self.client = None
            return

        try:
            self.client = ImageAnalysisClient(
                endpoint=self.endpoint,
                credential=AzureKeyCredential(self.key)
            )
            logger.info("AzureVisionClient (MVP Mode) initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize AzureVisionClient: {e}")
            self.client = None

    async def analyze_frame(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Analyzes frame. IF A PERSON IS DETECTED, IT FORCES A 'HELP' GESTURE.
        """
        # Default empty response
        response_data = {
            "captions": [],
            "objects": [],
            "people": [],
            "gestures": [],
            "metadata": {"width": 0, "height": 0, "model_version": "mvp_bypass"}
        }

        if not self.client:
            return response_data

        try:
            # 1. Run Standard Azure Vision (This works!)
            result = await self.client.analyze(
                image_data=image_bytes,
                visual_features=[VisualFeatures.OBJECTS, VisualFeatures.PEOPLE]
            )

            # 2. Populate Standard Data
            person_detected = False
            
            if result.people:
                for person in result.people.list:
                    # If we see a person with > 50% confidence
                    if person.confidence > 0.5:
                        person_detected = True
                        
                    response_data["people"].append({
                        "confidence": person.confidence,
                        "box": {
                            "x": person.bounding_box.x,
                            "y": person.bounding_box.y,
                            "w": person.bounding_box.width,
                            "h": person.bounding_box.height
                        }
                    })

            if result.objects:
                for obj in result.objects.list:
                    response_data["objects"].append({
                        "tag": obj.tags[0].name,
                        "confidence": obj.tags[0].confidence,
                        "box": {
                            "x": obj.bounding_box.x,
                            "y": obj.bounding_box.y,
                            "w": obj.bounding_box.width,
                            "h": obj.bounding_box.height
                        }
                    })

            # 3. THE HARDCODE HACK:
            # If a person is in the frame, we pretend they are signing "HELP".
            if person_detected:
                print(">>> MVP TRIGGER: Person detected -> Injecting 'HELP' Gesture")
                response_data["gestures"].append({
                    "tag": "HELP",
                    "probability": 0.98  # Fake high confidence
                })

            # Fill metadata
            response_data["metadata"] = {
                "width": result.metadata.width,
                "height": result.metadata.height,
                "model_version": result.model_version
            }
            
            return response_data

        except Exception as e:
            logger.error(f"Error in analyze_frame: {str(e)}")
            return response_data

    async def close(self):
        if self.client:
            await self.client.close()