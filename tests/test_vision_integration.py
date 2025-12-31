import asyncio
import os
import sys
from unittest.mock import MagicMock, patch

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Mock Azure SDKs
with patch('azure.ai.vision.imageanalysis.aio.ImageAnalysisClient') as MockAnalysisClient, \
     patch('azure.cognitiveservices.vision.customvision.prediction.CustomVisionPredictionClient') as MockCustomVisionClient:

    from services.vision_service import AzureVisionClient

    async def test_vision_integration():
        print("Starting Vision Integration Test...")
        
        # Setup Environment
        os.environ["AZURE_VISION_KEY"] = "mock_key"
        os.environ["AZURE_VISION_ENDPOINT"] = "https://mock.generated"
        os.environ["AZURE_CUSTOM_VISION_KEY"] = "mock_cv_key"
        os.environ["AZURE_CUSTOM_VISION_ENDPOINT"] = "https://mock.cv.generated"
        os.environ["AZURE_CUSTOM_VISION_PROJECT_ID"] = "mock_proj"
        os.environ["AZURE_CUSTOM_VISION_MODEL_NAME"] = "mock_model"

        # Initialize Client
        client = AzureVisionClient()
        
        # Mock Standard Vision Response (Caption + People)
        mock_vision_result = MagicMock()
        mock_vision_result.metadata.width = 1920
        mock_vision_result.metadata.height = 1080
        mock_vision_result.model_version = "2023-04-01-preview"
        
        mock_caption = MagicMock()
        mock_caption.text = "A person signaling for help in a room."
        mock_caption.confidence = 0.98
        mock_vision_result.caption = mock_caption
        
        mock_person = MagicMock()
        mock_person.confidence = 0.99
        mock_person.bounding_box.x = 100
        mock_person.bounding_box.y = 200
        mock_person.bounding_box.width = 300
        mock_person.bounding_box.height = 800
        mock_vision_result.people.list = [mock_person]
        mock_vision_result.objects.list = []

        # Make analyze return an awaitable future
        vision_future = asyncio.Future()
        vision_future.set_result(mock_vision_result)
        client.client.analyze.return_value = vision_future

        # Mock Custom Vision Response (HELP Gesture)
        mock_prediction = MagicMock()
        mock_prediction.tag_name = "HELP"
        mock_prediction.probability = 0.92
        mock_cv_result = MagicMock()
        mock_cv_result.predictions = [mock_prediction]
        
        # NOTE: client.custom_vision_client.predict_gesture uses asyncio.to_thread wrapped around a synchronous call
        # So we mock the synchronous classify_image method on the inner client
        client.custom_vision_client.client.classify_image.return_value = mock_cv_result

        # Mock Close
        close_future = asyncio.Future()
        close_future.set_result(None)
        client.client.close.return_value = close_future

        # Execute
        print("Analyzing frame (Simulating Person Signing 'Help')...")
        # Dummy image bytes
        image_bytes = b"fake_image_bytes" 
        result = await client.analyze_frame(image_bytes)

        # Verify
        print("Result Received:", result)
        
        # 1. Verify Description (Caption)
        caption_text = result["captions"][0]["text"]
        assert "help" in caption_text.lower(), "Caption should mention help"
        print(f"Verified Caption: {caption_text}")

        # 2. Verify Person Location
        people_count = len(result["people"])
        assert people_count > 0, "Should detect at least one person"
        person_box = result["people"][0]["box"]
        print(f"Verified Person Location: {person_box}")

        # 3. Verify Gesture
        gestures = result["gestures"]
        assert len(gestures) > 0, "Should detect gestures"
        assert gestures[0]["tag"] == "HELP", "Should detect HELP gesture"
        print(f"Verified Gesture: {gestures[0]['tag']} ({gestures[0]['probability']:.2f})")

        await client.close()
        print("Vision Integration Test Passed Successfully!")

    if __name__ == "__main__":
        asyncio.run(test_vision_integration())
