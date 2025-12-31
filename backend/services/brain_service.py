
import os
import logging
from google import genai
try:
    import azure.cognitiveservices.speech as speechsdk
except ImportError:
    speechsdk = None
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CrisisOrchestrator:
    """
    Orchestrates high-stress decision making using Google Gemini (gemini-2.5-flash).
    """
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.model_name = "gemini-2.5-flash"

        if not self.api_key:
            logger.warning("Gemini credentials missing! Feature will be disabled.")
            self.client = None
        else:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini Client: {e}")
                self.client = None
        
        # Speech Configuration
        self.speech_key = os.getenv("AZURE_SPEECH_KEY")
        self.speech_region = os.getenv("AZURE_SPEECH_REGION")
        self.speech_config = None
        if self.speech_key and self.speech_region and speechsdk:
            try:
                self.speech_config = speechsdk.SpeechConfig(subscription=self.speech_key, region=self.speech_region)
                self.speech_config.speech_synthesis_voice_name='en-US-AvaMultilingualNeural'
                logger.info("Azure Speech initialized.")
            except Exception as e:
                logger.error(f"Failed to config Azure Speech: {e}")
        else:
            logger.warning("Azure Speech credentials missing or SDK not installed. Speech module disabled.")

        logger.info(f"CrisisOrchestrator initialized with model: {self.model_name}")

    async def validate_context(self, vision_context: str, sign_detected: str) -> bool:
        """
        Uses LLM to check consistency between visual scene and sign detected.
        """
        prompt = (
            f"Visual Context: {vision_context}\n"
            f"Sign Detected: {sign_detected}\n"
            f"Is the sign consistent with the visual context? If the visual context is an immediate physical threat (fire, weapon) "
            f"and the sign is mismatched (e.g. asking for police instead of fire dept), consider it a stressful situation but valid emergency. "
            f"Return 'VALID' if the emergency is real/plausible. Return 'INVALID' only if it seems like a complete error."
        )
        if not self.client:
            logger.warning("Gemini Client not initialized. Skipping validation.")
            return True # Fail open

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            result = response.text.strip().upper()
            logger.info(f"Validation Result: {result}")
            return "VALID" in result
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return True # Fail open safely

    async def calculate_severity(self, vision_context: str, sign_detected: str) -> int:
        """
        Calculates a Severity Score (1-10).
        """
        prompt = (
            f"Visual Context: {vision_context}\n"
            f"Sign Detected: {sign_detected}\n"
            f"Rate the severity of this emergency on a scale of 1 to 10 (10 being immediate life threat).\n"
            f"Output ONLY the number."
        )
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            score_text = response.text.strip()
            # Extract number
            import re
            match = re.search(r'\d+', score_text)
            score = int(match.group()) if match else 5
            logger.info(f"Severity Score: {score}")
            return score
        except Exception as e:
            logger.error(f"Severity calculation failed: {e}")
            return 5 # Default moderate severity

    def trigger_speech_alert(self, text: str):
        """
        Stage 4: Synthesize speech.
        """
        logger.warning(f"SPEECH TRIGGERED: {text}")
        if self.speech_config and speechsdk:
            try:
                synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config, audio_config=None)
                result = synthesizer.speak_text_async(text).get()
                if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                    logger.info("Speech synthesized to audio stream/speaker data.")
                else:
                    logger.error(f"Speech synthesis canceled: {result.cancellation_details.reason}")
            except Exception as e:
                logger.error(f"Speech synthesis error: {e}")
        else:
            logger.info("Speech module skipped (not configured).")

    async def run_agentic_loop(self, vision_context: str, sign_detected: str, user_metadata: dict) -> dict:
        """
        Autonomous Agentic Loop:
        1. Validation
        2. Severity Check
        3. Action (Speech + SBAR)
        """
        logger.info(">>> Starting Agentic Loop <<<")
        
        # 1. Validation
        is_valid = await self.validate_context(vision_context, sign_detected)
        if not is_valid:
            logger.warning("Emergency validation returned INVALID. Aborting high alert.")
            return {"status": "ABORTED", "reason": "Context Mismatch"}

        # 2. Severity Score
        severity = await self.calculate_severity(vision_context, sign_detected)
        
        # 3. Action Logic
        if severity > 8:
            logger.warning("High Severity Detected! Bypassing confirmation.")
            speech_text = f"Emergency Alert! High severity incident detected at {user_metadata.get('location')}."
            loop = asyncio.get_event_loop()
            loop.run_in_executor(None, self.trigger_speech_alert, speech_text)
        
        # Generate SBAR (Stage 3 final output)
        report = await self.generate_dispatch_report(vision_context, user_metadata)
        
        return {
            "status": "COMPLETED",
            "severity": severity,
            "sbar_report": report,
            "speech_triggered": severity > 8
        }

    async def generate_dispatch_report(self, vision_context: str, user_metadata: dict) -> str:
        """
        Generates a concise SBAR report for 911 dispatch based on visual context and user metadata.
        Uses Gemini's thinking process to formulate a professional report.
        """
        location = user_metadata.get("location", "Unknown Location")
        name = user_metadata.get("name", "Unknown User")
        medical_history = user_metadata.get("medical_history", "None available")
        emergency_contact = user_metadata.get("emergency_contact", "None available")
        
        # Refined SBAR instructions
        prompt = (
            f"Analyze the visual scene {vision_context} and the user's medical history {medical_history}.\n"
            f"Generate a professional SBAR report for an emergency dispatcher. Keep it under 80 words.\n"
            f"YOU MUST USE THE FOLLOWING EXACT HEADERS (in uppercase):\n"
            f"SITUATION: [content]\n"
            f"BACKGROUND: [content]\n"
            f"ASSESSMENT: [content]\n"
            f"RECOMMENDATION: [content]\n\n"
            f"User Details:\n"
            f"Name: {name}\n"
            f"Location: {location}\n"
            f"Emergency Contact: {emergency_contact}"
        )

        if not self.client:
             return "SBAR Unavailable (Brain Offline)"

        try:
            # Using generate_content which supports thinking if the model supports it, 
            # though standard flash models might just produce the text.
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )

            report = response.text
            logger.info("SBAR Report generated successfully")
            return report

        except Exception as e:
            logger.error(f"Failed to generate SBAR report: {e}")
            return "CRITICAL ERROR: Failed to generate emergency report."
