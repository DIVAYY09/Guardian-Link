import asyncio
import base64
import json
import logging
import time
import os
from dotenv import load_dotenv

# Force load the .env file from the project root
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
print(f"Loading .env from: {env_path}")
load_dotenv(dotenv_path=env_path, override=True)
import time
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.services.vision_service import AzureVisionClient
from backend.agent_protocol import GuardianMasterAgent
from collections import deque
from enum import Enum

class EmergencyState(Enum):
    IDLE = "IDLE"
    CONFIRMED = "CONFIRMED"
    COOLDOWN = "COOLDOWN"

# Global State for Finite State Machine
SYSTEM_STATE = EmergencyState.IDLE
LAST_TRIGGER_TIME = 0.0
COOLDOWN_SECONDS = 30.0

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global Exception Handler for stability
import sys
import traceback

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

        return

    log_path = r"C:\Users\divay\OneDrive\Documents\guardianlink_runtime\logs\crash_log.txt"
    with open(log_path, "a") as f:
        f.write("\n" + "="*80 + "\n")
        f.write(f"CRASH TIMESTAMP: {time.ctime()}\n")
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
    
    logger.critical("Uncaught exception logged to crash_log.txt", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

app = FastAPI()

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5175', 'http://127.0.0.1:5175'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directory for audio files
# Mount static directory for audio files
import os
# Mount local static for assets if any
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")
# Mount Runtime Audio for Frontend Access
runtime_audio_dir = r"C:\Users\divay\OneDrive\Documents\guardianlink_runtime\audio"
os.makedirs(runtime_audio_dir, exist_ok=True)
app.mount("/runtime_audio", StaticFiles(directory=runtime_audio_dir), name="runtime_audio")

# Initialize Vision Client
vision_client = AzureVisionClient()
master_agent = GuardianMasterAgent()

# Global State for Temporal Logic
# Stores last 10 detected gesture tags
FRAME_HISTORY = deque(maxlen=10)

class Throttler:
    """
    Simple throttler to limit action frequency.
    """
    def __init__(self, interval_seconds: float):
        self.interval = interval_seconds
        self.last_action_time = 0.0

    def allow(self) -> bool:
        current_time = time.time()
        if current_time - self.last_action_time >= self.interval:
            self.last_action_time = current_time
            return True
        return False

# Global throttler: 1 frame per second
frame_throttler = Throttler(interval_seconds=1.0)

@app.on_event("startup")
async def startup_event():
    """Ensure resources are initialized on startup if needed."""
    logger.info("Guardian-Link Backend Started")

@app.on_event("shutdown")
async def shutdown_event():
    """Close vision client on shutdown."""
    await vision_client.close()

@app.get("/")
def read_root():
    return {"Hello": "Guardian-Link Backend"}

@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection established")
    
    try:
        while True:
            # Receive base64 encoded frame
            data = await websocket.receive_text()
            print('Frame received from Frontend') # User requested validation log
            
            
            # Check throttler
            if not frame_throttler.allow():
                # Allow pings even if throttled (though pings usually small, let's parse first)
                pass

            try:
                # Decode base64 or JSON
                # Check if it's a JSON heartbeat
                if data.startswith("{") and "ping" in data:
                    try:
                        message = json.loads(data)
                        if message.get("type") == "ping":
                            await websocket.send_json({"type": "pong"})
                            continue
                    except:
                        pass # Not a JSON ping, treat as image
                
                if not frame_throttler.allow():
                     continue
                     
                # Diagnostic Log
                print(f"Frames in buffer: {len(FRAME_HISTORY)}")

                # Expected format: "data:image/jpeg;base64,....." or just raw base64
                if "," in data:
                    header, encoded = data.split(",", 1)
                else:
                    encoded = data
                
                image_bytes = base64.b64decode(encoded)
                
                # Analyze frame
                try:
                    results = await vision_client.analyze_frame(image_bytes)
                except Exception as e:
                    logger.error(f"Vision Service Failed: {e}")
                    # Fallback Mode for Vision
                    await websocket.send_json({
                        "status": "fallback",
                        "sign": "Unknown",
                        "caption": "Vision System Offline - Checking Connection...",
                        "sbar": "",
                        "audio_ready": False
                    })
                    continue

                # --- Temporal Logic: Update Frame History ---
                gestures = results.get("gestures", [])
                
                # Determine primary tag
                current_tag = "Neutral"
                if gestures:
                    best_gesture = max(gestures, key=lambda x: x['probability'])
                    if best_gesture['probability'] > 0.5:
                        current_tag = best_gesture['tag']
                
                FRAME_HISTORY.append(current_tag)
                
                # Get Caption
                scene_caption = "Monitoring..."
                if results.get("captions"):
                    scene_caption = results["captions"][0]["text"]

                # --- Emergency Trigger Check ---
                help_count = FRAME_HISTORY.count("HELP")
                emergency_triggered = False
                
                if len(FRAME_HISTORY) == FRAME_HISTORY.maxlen and help_count > 7:
                    emergency_triggered = True

                # Construction Standardized Response
                response_payload = {
                    "status": "alert" if emergency_triggered else "monitoring",
                    "sign": current_tag,
                    "caption": scene_caption,
                    "sbar": "",
                    "audio_ready": False
                }

                # --- Hysteresis & State Machine ---
                current_time = time.time()
                global SYSTEM_STATE, LAST_TRIGGER_TIME
                
                # Auto-reset state if cooldown passed
                if SYSTEM_STATE != EmergencyState.IDLE:
                    if (current_time - LAST_TRIGGER_TIME) > COOLDOWN_SECONDS:
                        SYSTEM_STATE = EmergencyState.IDLE
                        logger.info("System State Reset to IDLE (Cooldown Complete)")

                if emergency_triggered:
                    if SYSTEM_STATE == EmergencyState.IDLE:
                        logger.warning("EMERGENCY TRIGGERED - CONFIRMED")
                        SYSTEM_STATE = EmergencyState.CONFIRMED
                        LAST_TRIGGER_TIME = current_time
                    else:
                        # Suppress trigger
                        emergency_triggered = False
                        # Optional: Log suppression if verbose
                        # logger.info(f"Trigger suppressed. State: {SYSTEM_STATE}")

                if emergency_triggered:
                    logger.warning("EXECUTING EMERGENCY PROTOCOL")
                    
                    try:
                        # Mock User Metadata
                        try:
                            with open("user_profile.json", "r") as f:
                                user_metadata = json.load(f)
                        except FileNotFoundError:
                            user_metadata = {"name": "Unknown", "location": "Unknown"}
                        
                        user_metadata["location"] = "37.7749, -122.4194 (Mock GPS)"
                        
                        # Call Master Agent
                        agent_response = await master_agent.process_emergency(scene_caption, user_metadata)
                        
                        response_payload["sbar"] = agent_response.get("sbar_preview", "Generating Report...")
                        response_payload["audio_ready"] = (agent_response.get("call_status") == "CALL_PLACED")
                        
                        # Apply Agent Feedback to caption if available
                        if agent_response.get("user_feedback"):
                            response_payload["caption"] = agent_response["user_feedback"]

                    except Exception as e:
                        logger.error(f"Agent/Brain Failure: {e}")
                        response_payload["status"] = "fallback"
                        response_payload["caption"] = "Brain Offline - Dispatching Standard Alert"
                        response_payload["sbar"] = "SYSTEM FAILURE: Manual Dispatch Required."

                # Send formatted JSON
                await websocket.send_json(response_payload)
                
            except Exception as e:
                logger.error(f"Error processing frame: {e}")
                await websocket.send_json({
                    "status": "fallback",
                    "sign": "Error",
                    "caption": "System Error - Processing Halted",
                    "sbar": str(e),
                    "audio_ready": False
                })
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")

