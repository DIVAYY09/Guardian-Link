import asyncio
from typing import Dict, Any, Optional, List
from backend.services.brain_service import CrisisOrchestrator
from backend.services.speech_service import GuardianVoiceClient
import logging

logger = logging.getLogger(__name__)

class GuardianMasterAgent:
    """
    Guardian Master Agent orchestrates the lifecycle of emergency response:
    1. Perception: Interface with Azure AI Vision and analyze for high alert triggers.
    2. Reasoning: Process input via Azure OpenAI to generate an emergency SBAR report.
    3. Action: Trigger Azure Speech synthesis and a mock Dispatcher Alert.
    """

    def __init__(self):
        # 0. Check for Mock Mode
        import os
        self.MOCK_MODE = not os.getenv("GOOGLE_API_KEY")
        if self.MOCK_MODE:
            logger.warning("[!] GOOGLE_API_KEY not found. Starting GuardianMasterAgent in MOCK_MODE.")

        # Initialize Crisis Orchestrator
        try:
            if not self.MOCK_MODE:
                self.crisis_orchestrator = CrisisOrchestrator()
                logger.info("Crisis Orchestrator attached to Master Agent.")
            else:
                 self.crisis_orchestrator = None
                 logger.info("Crisis Orchestrator disabled (Mock Mode).")
        except Exception as e:
            logger.error(f"Failed to initialize Crisis Orchestrator: {e}")
            self.crisis_orchestrator = None
            
        try:
            self.voice_client = GuardianVoiceClient()
            logger.info("Guardian Voice Client attached to Master Agent.")
        except Exception as e:
            logger.error(f"Failed to initialize Voice Client: {e}")
            self.voice_client = None

        self.gesture_history: List[Dict[str, Any]] = []
        self.pending_dispatch_call: Optional[str] = None

    def interpret_gesture_sequence(self, results_history: List[Dict[str, Any]]) -> Optional[str]:
        """
        Agentic Reasoning Layer:
        Analyzes the last 5 frames to determine if a consistent emergency pattern is emerging.
        
        Args:
            results_history: List of analysis results from the last few frames.
            
        Returns:
            Optional[str]: 'HIGH_ALERT_GESTURE' if a pattern is confirmed, else None.
        """
        if len(results_history) < 5:
            return None
        
        # Check for 'HELP' gesture consistency
        help_count = 0
        for result in results_history[-5:]:
            gestures = result.get("gestures", [])
            for gesture in gestures:
                if gesture.get("tag") == "HELP" and gesture.get("probability", 0) > 0.7:
                    help_count += 1
        

        
        if help_count >= 3:
            return "HIGH_ALERT_GESTURE: Consistent 'HELP' signal detected."
        
        return None

    async def perceive_environment(self, image_data: Any) -> Dict[str, Any]:
        """
        Stage 1: Interface with Azure AI Vision.
        Checks for specific keywords or gesture patterns to trigger High Alert.
        """
        print(f"[Perception] Analyzing visual input: {image_data}")
        
        # Mocking the analysis result structure coming from Vision Service
        # In a real integration, image_data would be processed by AzureVisionClient
        
        analysis_result = {}
        
        # Check if we are receiving mock data (dict) or actual image data
        if isinstance(image_data, dict):
            analysis_result = image_data
        else:
            # TODO: Implement actual Azure AI Vision API call here
            # For now, return mock
            await asyncio.sleep(1) # Simulate network delay
            analysis_result = {
                "description": "Mock perception data: Person detected falling.", 
                "confidence": 0.95,
                "objects": [{"tag": "person", "confidence": 0.9}],
                "captions": [{"text": "A person falling on the floor", "confidence": 0.95}],
                "gestures": [], # No gesture in this mock default
                "timestamp": "2023-01-01T12:00:00Z"
            }

        # --- Agentic Reasoning Trigger Logic ---
        alert_status = "NORMAL"
        alert_reason = ""

        # 1. Keyword Spotting in Captions/Objects
        emergency_keywords = ["fire", "smoke", "weapon", "gun", "knife", "person falling", "choking"]
        
        # Check captions
        for caption in analysis_result.get("captions", []):
            text = caption.get("text", "").lower()
            for keyword in emergency_keywords:
                if keyword in text:
                    alert_status = "HIGH_ALERT"
                    alert_reason = f"Keyword detected: {keyword}"
                    break
        
        # Check objects if not already high alert
        if alert_status == "NORMAL":
            for obj in analysis_result.get("objects", []):
                tag = obj.get("tag", "").lower()
                if tag in emergency_keywords:
                    alert_status = "HIGH_ALERT"
                    alert_reason = f"Object detected: {tag}"
                    break

        # 2. Gesture Sequence Reasoning
        # Add current result to history (mocking the structure)
        self.gesture_history.append(analysis_result)
        if len(self.gesture_history) > 10:
            self.gesture_history.pop(0) # Keep history size manageable
            
        gesture_alert = self.interpret_gesture_sequence(self.gesture_history)
        if gesture_alert:
            alert_status = "HIGH_ALERT"
            alert_reason = gesture_alert

        # Enrich the result with alert status
        analysis_result["alert_status"] = alert_status
        analysis_result["alert_reason"] = alert_reason
        
        if alert_status == "HIGH_ALERT":
            print(f"!!! [Perception] HIGH ALERT TRIGGERED: {alert_reason} !!!")

        return analysis_result

    async def analyze_situation(self, perception_data: Dict[str, Any]) -> str:
        """
        Stage 2: Process input via Azure OpenAI to generate an SBAR report.
        """
        print("[Reasoning] Generating SBAR report...")
        description = perception_data.get("description", "Unknown Event")
        alert_status = perception_data.get("alert_status", "NORMAL")
        alert_reason = perception_data.get("alert_reason", "None")
        
        if perception_data.get("captions") and len(perception_data["captions"]) > 0:
             description = perception_data["captions"][0]["text"]

        # TODO: Implement Azure OpenAI API call to generate SBAR based on perception_data
        
        # Dynamic Mock SBAR generation based on input
        sbar_report = (
            f"SITUATION: {alert_status} - {alert_reason}\n"
            f"BACKGROUND: Visual monitoring active. {description}\n"
            f"ASSESSMENT: System analysis indicates {alert_reason.lower()} with high confidence.\n"
            "RECOMMENDATION: " + ("Activate emergency response." if alert_status == "HIGH_ALERT" else "Continue monitoring.")
        )
        await asyncio.sleep(1) # Simulate processing time
        return sbar_report

    async def execute_response(self, sbar_report: str) -> None:
        """
        Stage 3: Trigger Azure Speech synthesis and a mock Dispatcher Alert.
        """
        print("[Action] Executing response protocols...")
        
        # TODO: Implement Azure Speech Synthesis to vocalize the alert
        
        # Mock Dispatcher Alert
        self._send_dispatcher_alert(sbar_report)
        await asyncio.sleep(0.5)

    def _send_dispatcher_alert(self, message: str) -> None:
        """
        Mock Dispatcher Alert mechanism.
        """
        print("\n!!! DISPATCHER ALERT TRIGGERED !!!")
        print("=" * 40)
        print(message)
        print("=" * 40)
        print("Alert successfully routed to Emergency Services Dashboard.\n")

    async def run_mission(self, image_input: Any = None) -> None:
        """
        Main orchestration loop to run the agent's mission.
        """
        print(">>> Guardian Master Agent: Mission Start")
        
        # 1. Perception
        perception_result = await self.perceive_environment(image_input)
        
        # 2. Reasoning
        sbar = await self.analyze_situation(perception_result)
        
        # 3. Action
        await self.execute_response(sbar)
        
    async def process_emergency(self, vision_context: str, user_metadata: Dict[str, Any], sign_detected: str = "HELP") -> Dict[str, str]:
        """
        Handles the emergency workflow when TRIGGERED.
        Uses CrisisOrchestrator's Agentic Loop.
        """
        logger.warning(f"PROCESSING EMERGENCY: {vision_context} | Sign: {sign_detected}")
        
        # User Feedback (Immediate)
        feedback_message = "Help is on the way. Stay calm."
        sbar_preview = "Pending..."
        
        if self.crisis_orchestrator:
            # Run Agentic Loop
            result = await self.crisis_orchestrator.run_agentic_loop(
                vision_context=vision_context, 
                sign_detected=sign_detected, 
                user_metadata=user_metadata
            )
            
            if result["status"] == "COMPLETED":
                self.pending_dispatch_call = result["sbar_report"]
                sbar_preview = f"[Severity {result['severity']}] {self.pending_dispatch_call}"
                
                audio_url = None
                call_status = None
                
                # Check for high severity to trigger voice
                if result.get("severity", 0) > 8:
                    if self.voice_client:
                        try:
                            # Generate audio
                            # Note: In production this should be awaited in background or handled better to not block
                            # But for this prototype we await it
                            audio_path = await self.voice_client.synthesize_sbar_to_audio(self.pending_dispatch_call)
                            # Assuming static mount is at /static/emergency_call.wav (since filename is fixed in service)
                            # But let's be dynamic if service changes, though service returns absolute path.
                            # We know main.py mounts backend/static at /static
                            # Filename is emergency_call.wav
                            audio_url = "/runtime_audio/emergency_call.wav"
                            call_status = "CALL_PLACED"
                            feedback_message += " (Voice Alert Broadcasted)"
                        except Exception as e:
                            logger.error(f"Voice generation failed: {e}")
                            call_status = "FAILED"
                    else:
                        logger.warning("Voice client not initialized, skipping audio.")
                
                # Return extended info
                return {
                    "user_feedback": feedback_message,
                    "sbar_preview": sbar_preview,
                    "call_status": call_status,
                    "audio_url": audio_url
                }

            else:
                sbar_preview = f"Alert Aborted: {result.get('reason')}"
                feedback_message = "Alert cancelled. Please confirm emergency."
                
            logger.info(f"Agentic Loop Result: {result['status']}")
        else:
            logger.error("Crisis Orchestrator not available.")
            sbar_preview = "Error: Crisis Brain Unavailable."
            
        return {
            "user_feedback": feedback_message,
            "sbar_preview": sbar_preview
        }

    # Keep existing run_mission but it's largely superseded by main.py's direct calls now

# Boilerplate for running the agent directly
if __name__ == "__main__":
    agent = GuardianMasterAgent()
    # Mocking a sequence to test gesture reasoning directly (simulating 5 frames)
    print("--- Testing Gesture Sequence ---")
    mock_frame_help = {"gestures": [{"tag": "HELP", "probability": 0.8}]}
    mock_frame_none = {"gestures": []}
    
    asyncio.run(agent.run_mission(mock_frame_help))
    asyncio.run(agent.run_mission(mock_frame_help))
    asyncio.run(agent.run_mission(mock_frame_none))
    asyncio.run(agent.run_mission(mock_frame_help)) # Should trigger high alert potentially if logic allows, or next one
    asyncio.run(agent.run_mission(mock_frame_help)) # 4th help in 5 frames -> High Alert

