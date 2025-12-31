import os
import logging
import asyncio
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from azure.ai.vision.imageanalysis.aio import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential
from azure.cognitiveservices.vision.customvision.prediction import CustomVisionPredictionClient
from msrest.authentication import ApiKeyCredentials
from azure.core.exceptions import HttpResponseError

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AzureCustomVisionClient:
    """
    Client for interacting with Azure Custom Vision prediction endpoint.
    Retrieves project configuration from environment variables.
    """
    def __init__(self):
        self.endpoint = os.getenv("AZURE_CUSTOM_VISION_ENDPOINT")
        print(f"DEBUG CHECK: Custom Vision Key found? {bool(os.getenv('AZURE_CUSTOM_VISION_KEY'))}")
        self.key = os.getenv("AZURE_CUSTOM_VISION_KEY")
        self.project_id = os.getenv("AZURE_CUSTOM_VISION_PROJECT_ID")
        self.model_name = os.getenv("AZURE_CUSTOM_VISION_ITERATION_NAME")

        if not all([self.endpoint, self.key, self.project_id, self.model_name]):
            logger.warning("Azure Custom Vision credentials/config missing. Feature will be disabled.")
            self.client = None
        else:
            try:
                credentials = ApiKeyCredentials(in_headers={"Prediction-Key": self.key})
                self.client = CustomVisionPredictionClient(endpoint=self.endpoint, credentials=credentials)
                logger.info("AzureCustomVisionClient initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize AzureCustomVisionClient: {e}")
                self.client = None

    async def predict_gesture(self, image_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Predicts gestures/signs from the image using Custom Vision.
        Looks for tags like 'HELP', 'FIRE', 'CHOKING'.
        """
        if not self.client:
            return []

        try:
            # The Custom Vision SDK is synchronous, so we run it in a separate thread
            # to avoid blocking the async event loop.
            results = await asyncio.to_thread(
                self.client.classify_image,
                self.project_id,
                self.model_name,
                image_bytes
            )

            gestures = []
            for prediction in results.predictions:
                # Filter by probability threshold if needed, e.g., > 50%
                if prediction.probability > 0.5:
                    gestures.append({
                        "tag": prediction.tag_name,
                        "probability": prediction.probability
                    })
            return gestures

        except Exception as e:
            logger.error(f"Error during gesture prediction: {e}")
            return []

class AzureVisionClient:
    """
    Client for interacting with Azure AI Vision service (Image Analysis 4.0).
    """
    def __init__(self):
        self.endpoint = os.getenv("AZURE_VISION_ENDPOINT")
        self.key = os.getenv("AZURE_VISION_KEY")

        if not self.endpoint or not self.key:
            logger.warning("Azure Vision credentials missing. Running in DEGRADED MODE (Offline Perception).")
            # Don't raise, just let client be None
            self.client = None
            self.custom_vision_client = None
            return

        try:
            self.client = ImageAnalysisClient(
                endpoint=self.endpoint,
                credential=AzureKeyCredential(self.key)
            )
            self.custom_vision_client = AzureCustomVisionClient()
            logger.info("AzureVisionClient initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize AzureVisionClient: {e}")
            # Degraded mode
            self.client = None

    async def analyze_frame(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Analyzes an image frame to detect objects, people, and generate captions.
        Also runs custom vision prediction for emergency gestures.

        Args:
            image_bytes (bytes): The image data in bytes.

        Returns:
            Dict[str, Any]: A dictionary containing the analysis results.
        """
        try:
            # Check for degraded mode
            if not self.client:
                # Return empty/mock result
                return {
                    "captions": [{"text": "Vision System Offline (Degraded Mode)", "confidence": 0.0}],
                    "objects": [],
                    "people": [],
                    "gestures": [],
                    "metadata": {"width": 0, "height": 0, "model_version": "offline"}
                }

            # Create concurrent tasks for both services
            vision_coro = self.client.analyze(
                image_data=image_bytes,
                visual_features=[
                    VisualFeatures.OBJECTS,
                    VisualFeatures.PEOPLE,
                ]
            )
            
            # Wrap in wait_for to prevent hang
            vision_task = asyncio.create_task(asyncio.wait_for(vision_coro, timeout=2.0))
            gesture_task = self.custom_vision_client.predict_gesture(image_bytes)

            # Wait for both to complete
            vision_result, gestures = await asyncio.gather(vision_task, gesture_task)

            # Process and format the results
            response_data = {
                "captions": [],
                "objects": [],
                "people": [],
                "gestures": gestures,
                "metadata": {
                    "width": vision_result.metadata.width,
                    "height": vision_result.metadata.height,
                    "model_version": vision_result.model_version
                }
            }

            if vision_result.caption:
                response_data["captions"].append({
                    "text": vision_result.caption.text,
                    "confidence": vision_result.caption.confidence
                })

            if vision_result.objects:
                for obj in vision_result.objects.list:
                    response_data["objects"].append({
                        "tag": obj.tags[0].name if obj.tags else "unknown",
                        "confidence": obj.tags[0].confidence if obj.tags else 0.0,
                        "box": {
                            "x": obj.bounding_box.x,
                            "y": obj.bounding_box.y,
                            "w": obj.bounding_box.width,
                            "h": obj.bounding_box.height
                        }
                    })

            if vision_result.people:
                for person in vision_result.people.list:
                    response_data["people"].append({
                        "confidence": person.confidence,
                        "box": {
                            "x": person.bounding_box.x,
                            "y": person.bounding_box.y,
                            "w": person.bounding_box.width,
                            "h": person.bounding_box.height
                        }
                    })
            
            return response_data

        except HttpResponseError as e:
            logger.error(f"Azure API HTTP error: {e.status_code} - {e.reason} - {e.message}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during image analysis: {str(e)}")
            raise

    async def close(self):
        """Close the underlying client session."""
        await self.client.close()
