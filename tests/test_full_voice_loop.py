import sys
import os
import asyncio

# Adjust path to import backend services
# Current file is in tests/, so we go up one level to root, then can import backend.
# Actually, if run from root, sys.path might be okay, but being safe:
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now we need to make sure we can import from backend. 
# Since backend is a package (has __init__? maybe not), or just a folder.
# The previous imports were `from services...` assuming backend was in path or run from backend.
# Let's import from backend.services.speech_service
try:
    from backend.services.speech_service import GuardianVoiceClient
except ImportError:
    # If standard import fails, try appending backend directory specifically
    sys.path.append(os.path.join(project_root, 'backend'))
    from services.speech_service import GuardianVoiceClient

async def test_loop():
    print("Initializing GuardianVoiceClient...")
    try:
        client = GuardianVoiceClient()
    except Exception as e:
        print(f"Failed to initialize client: {e}")
        return

    sbar_text = "SITUATION: Heart attack. BACKGROUND: Asthmatic male. ASSESSMENT: Critical. RECOMMENDATION: Send ambulance."
    print(f"Mock SBAR Report: {sbar_text}")

    print("Generating audio...")
    try:
        file_path = await client.synthesize_sbar_to_audio(sbar_text)
        print(f"Audio generated at: {file_path}")

        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"File size: {size} bytes")
            if size > 0:
                print("SUCCESS")
                
                # Command to play audio
                print("\nTo play the audio, run this command in your terminal:")
                print(f'start "" "{file_path}"') 
            else:
                print("FAILED: File is empty")
        else:
            print("FAILED: File not found")

    except Exception as e:
        print(f"Error during synthesis: {e}")

if __name__ == "__main__":
    asyncio.run(test_loop())
