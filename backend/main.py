import asyncio
import base64
import json
import logging
import time
import os
import sys
from typing import Optional
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# ==========================================
# CRITICAL FIX: PATH RESOLUTION
# ==========================================
# Get the absolute path of the 'backend' directory
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the project root (parent of 'backend')
project_root = os.path.dirname(current_dir)

# Force add the project root to sys.path
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"[BOOT] Added project root to sys.path: {project_root}")
# ==========================================

# Force load the .env file from the project root
env_path = os.path.join(project_root, '.env')
print(f"Loading .env from: {env_path}")
load_dotenv(dotenv_path=env_path, override=True)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.services.vision_service import AzureVisionClient
from backend.agent_protocol import GuardianMasterAgent
from collections import deque
from enum import Enum
import traceback

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

# Global Exception Handler
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    log_dir = os.path.join(project_root, "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "crash_log.txt")
    
    with open(log_path, "a") as f:
        f.write("\n" + "="*80 + "\n")
        f.write(f"CRASH TIMESTAMP: {time.ctime()}\n")
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
    
    logger.critical(f"Uncaught exception logged to {log_path}", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

# Initialize Clients Global Scope
vision_client = AzureVisionClient()
master_agent = GuardianMasterAgent()

# --- LIFESPAN HANDLER (Replaces on_event) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup Logic
    logger.info("Guardian-Link Backend Started")
    yield
    # Shutdown Logic
    logger.info("Guardian-Link Backend Shutting Down...")
    await vision_client.close()

# Initialize App with Lifespan
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5175', 'http://127.0.0.1:5175', '*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount local static for assets if any
app.mount("/static", StaticFiles(directory=os.path.join(current_dir, "static")), name="static")

# Mount Runtime Audio
runtime_audio_dir = os.path.join(project_root, "runtime_audio")
os.makedirs(runtime_audio_dir, exist_ok=True)
app.mount("/runtime_audio", StaticFiles(directory=runtime_audio_dir), name="runtime_audio")

FRAME_HISTORY = deque(maxlen=10)

class Throttler:
    def __init__(self, interval_seconds: float):
        self.interval = interval_seconds
        self.last_action_time = 0.0

    def allow(self) -> bool:
        current_time = time.time()
        if current_time - self.last_action_time >= self.interval:
            self.last_action_time = current_time
            return True
        return False

# Global throttler
frame_throttler = Throttler(interval_seconds=1.0)

@app.get("/")
def read_root():
    return {"Hello": "Guardian-Link Backend"}

@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection established")
    
    try:
        while True:
            # Receive data
            data = await websocket.receive_text()
            
            # Check for ping before throttling
            if data.startswith("{") and "ping" in data:
                try:
                    message = json.loads(data)
                    if message.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                        continue
                except:
                    pass 

            # Apply Throttling for frame processing
            if not frame_throttler.allow():
                 continue
                 
            try:
                if "," in data:
                    header, encoded = data.split(",", 1)
                else:
                    encoded = data
                
                image_bytes = base64.b64decode(encoded)
                
                # Analyze frame
                results = await vision_client.analyze_frame(image_bytes)

                # --- Temporal Logic ---
                gestures = results.get("gestures", [])
                current_tag = "Neutral"
                if gestures:
                    best_gesture = max(gestures, key=lambda x: x['probability'])
                    if best_gesture['probability'] > 0.5:
                        current_tag = best_gesture['tag']
                
                FRAME_HISTORY.append(current_tag)
                
                scene_caption = "Monitoring..."
                if results.get("captions"):
                    scene_caption = results["captions"][0]["text"]

                # --- Emergency Trigger Check ---
                help_count = FRAME_HISTORY.count("HELP")
                emergency_triggered = False
                
                if len(FRAME_HISTORY) == FRAME_HISTORY.maxlen and help_count > 7:
                    emergency_triggered = True

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
                
                if SYSTEM_STATE != EmergencyState.IDLE:
                    if (current_time - LAST_TRIGGER_TIME) > COOLDOWN_SECONDS:
                        SYSTEM_STATE = EmergencyState.IDLE
                        logger.info("System State Reset to IDLE")

                if emergency_triggered:
                    if SYSTEM_STATE == EmergencyState.IDLE:
                        logger.warning("EMERGENCY TRIGGERED - CONFIRMED")
                        SYSTEM_STATE = EmergencyState.CONFIRMED
                        LAST_TRIGGER_TIME = current_time
                    else:
                        emergency_triggered = False

                if emergency_triggered:
                    logger.warning("EXECUTING EMERGENCY PROTOCOL")
                    try:
                        user_profile_path = os.path.join(current_dir, "user_profile.json")
                        try:
                            with open(user_profile_path, "r") as f:
                                user_metadata = json.load(f)
                        except:
                            user_metadata = {"name": "Unknown", "location": "Unknown"}
                        
                        user_metadata["location"] = "37.7749, -122.4194 (Mock GPS)"
                        
                        agent_response = await master_agent.process_emergency(scene_caption, user_metadata)
                        
                        response_payload["sbar"] = agent_response.get("sbar_preview", "Generating Report...")
                        response_payload["audio_ready"] = (agent_response.get("call_status") == "CALL_PLACED")
                        if agent_response.get("user_feedback"):
                            response_payload["caption"] = agent_response["user_feedback"]

                    except Exception as e:
                        logger.error(f"Agent/Brain Failure: {e}")
                        response_payload["status"] = "fallback"
                        response_payload["sbar"] = "SYSTEM FAILURE: Manual Dispatch Required."

                await websocket.send_json(response_payload)
                
            except Exception as e:
                # Catch processing errors but KEEP CONNECTION ALIVE
                logger.error(f"Frame processing error: {e}")
                await websocket.send_json({
                    "status": "fallback",
                    "caption": "System Error - Retrying...",
                })
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket fatal error: {e}")