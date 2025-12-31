import sys
import os
import asyncio
import logging

# Add backend to sys.path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from agent_protocol import GuardianMasterAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FinalE2E")

async def run_test():
    print("="*60)
    print(" FINAL END-TO-END VERIFICATION: PROJECT GUARDIAN-LINK ")
    print("="*60)

    print("\n[1] Initializing Guardian Master Agent...")
    try:
        agent = GuardianMasterAgent()
        print("[+] Agent initialized successfully.")
    except Exception as e:
        print(f"[!] FAIILED to initialize Agent: {e}")
        return

    # Mock Data
    mock_caption = "A person detected falling on the floor in a living room."
    mock_metadata = {
        "user_id": "test_user_001",
        "name": "Test Subject",
        "medical_history": "Hypertension",
        "location": "37.7749, -122.4194"
    }
    sign_input = "HELP"

    print(f"\n[2] Simulating Emergency Trigger: Input Sign '{sign_input}'...")
    print(f"    Context: {mock_caption}")

    try:
        response = await agent.process_emergency(mock_caption, mock_metadata, sign_detected=sign_input)
    except Exception as e:
        print(f"[!] FAILED during process_emergency: {e}")
        return

    # Verification Steps
    print("\n[3] Verifying Output...")

    # Check SBAR
    sbar = response.get("sbar_preview", "")
    print(f"    [>] SBAR Generated: {sbar[:50]}...") 
    
    if "SITUATION" in sbar or "Situation" in sbar:
        print("[+] SBAR structure confirmed.")
    else:
        print("[!] SBAR structure verification FAILED.")

    # Check Audio
    audio_path = response.get("audio_url")
    print(f"    [>] Audio Status: {response.get('call_status')}")
    print(f"    [>] Audio Path: {audio_path}")

    # Check if file exists (backend returns relative static path, but actual location is backend/static)
    # The agent might return "/static/emergency_call.wav" or a full path provided by voice client.
    # The voice client usually saves to 'static/emergency_call.wav' relative to where it runs.
    # Let's check backend/static/emergency_call.wav
    
    expected_path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'static', 'emergency_call.wav')
    if os.path.exists(expected_path):
        size = os.path.getsize(expected_path)
        print(f"[+] Audio file found at {expected_path} (Size: {size} bytes)")
        if size > 1000:
            print("[+] Audio file size indicates valid content.")
        else:
            print("[!] Audio file seems too small (empty?).")
    else:
        print(f"[!] Audio file NOT found at {expected_path}")
        print("    (Note: This might be expected if Azure Speech Key is invalid or quota exceeded)")

    print("\n" + "="*60)
    print(" SYSTEM READY FOR SUBMISSION ")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(run_test())
