import os
import logging
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class GuardianVoiceClient:
    """
    Handles speech synthesis for Guardian emergencies using Azure Speech Services.
    """
    def __init__(self):
        self.speech_key = os.getenv("AZURE_SPEECH_KEY")
        self.speech_region = os.getenv("AZURE_SPEECH_REGION")
        
        if not self.speech_key or not self.speech_region:
            logger.error("Azure Speech credentials missing.")
            raise ValueError("Missing AZURE_SPEECH_KEY or AZURE_SPEECH_REGION")

        try:
            self.speech_config = speechsdk.SpeechConfig(
                subscription=self.speech_key, 
                region=self.speech_region
            )
            # Set default voice (though SSML overrides this usually, it's good practice)
            self.speech_config.speech_synthesis_voice_name = "en-US-AvaNeural"
            
            # Configure audio output to file
            # Configure audio output to decoupled runtime folder
            self.static_dir = r"C:\Users\divay\OneDrive\Documents\guardianlink_runtime\audio"
            os.makedirs(self.static_dir, exist_ok=True)
            self.output_file = os.path.join(self.static_dir, "emergency_call.wav")
            
            self.audio_config = speechsdk.audio.AudioOutputConfig(filename=self.output_file)
            
            self.synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config, 
                audio_config=self.audio_config
            )
            logger.info("GuardianVoiceClient initialized.")
            
        except Exception as e:
            logger.error(f"Failed to initialize Azure Speech: {e}")
            raise

    async def synthesize_sbar_to_audio(self, sbar_text: str) -> str:
        """
        Synthesizes the SBAR report into an emergency audio file using SSML.
        Returns the path to the generated wav file.
        """
        logger.info("Synthesizing SBAR to audio...")
        
        # XML-escape special characters in text to avoid SSML errors
        safe_text = sbar_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        ssml_string = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
            <voice name="en-US-AvaNeural">
                <prosody rate="fast" volume="loud">
                    {safe_text}
                </prosody>
            </voice>
        </speak>
        """

        try:
            # Azure Speech SDK synthesis is blocking, but fast enough for this scope. 
            # Ideally running in executor if high load, but acceptable here.
            result = self.synthesizer.speak_ssml_async(ssml_string).get()

            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                logger.info(f"Audio saved to {self.output_file}")
                return self.output_file
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                logger.error(f"Speech synthesis canceled: {cancellation_details.reason}")
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    logger.error(f"Error details: {cancellation_details.error_details}")
                raise RuntimeError("Speech synthesis failed.")
            else:
                 raise RuntimeError(f"Unexpected result reason: {result.reason}")

        except Exception as e:
            logger.error(f"Error in synthesize_sbar_to_audio: {e}")
            raise
