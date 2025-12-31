# Guardian-Link

Guardian-Link is an intelligent emergency response system that leverages Azure AI to detect, analyze, and respond to critical situations in real-time.

## Project Structure
- **/backend**: FastAPI application for processing streams and agent logic.
- **/frontend**: React application for camera streaming and UI.
- **/docs**: Documentation.

## Getting Started
1. Setup `.env` in backend.
2. Run backend: `uvicorn main:app --reload`.
3. Run frontend: `npm run dev`.

## Stage 2: Vision Success
**Status**: Verified ✅

The system successfully integrates Azure AI Vision and Custom Vision to analyze live video feeds.
- **Flow**:
    1. **Source**: React Frontend captures user webcam feed.
    2. **Transport**: Frames are sent via WebSocket (`/ws/stream`) to the FastAPI backend.
    3. **Processing**: Backend throttles requests (1 FPS) and forwards frames to Azure.
    4. **Analysis**: 
        - **Azure AI Vision**: Detects people, objects, and provides scene captions.
        - **Custom Vision**: Identifies specific emergency gestures (e.g., 'HELP').
    5. **Feedback**: Results are streamed back to the frontend and overlaid on the video in real-time.

**Verification**:
Run `python tests/test_vision_integration.py` to confirm the pipeline correctly identifies a person signing 'Help' and returns their location.
