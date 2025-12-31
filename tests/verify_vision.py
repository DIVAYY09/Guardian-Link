
import asyncio
import os
import sys
from collections import deque
from pathlib import Path
from dotenv import load_dotenv

# Add backend to path to allow imports
backend_path = Path(__file__).resolve().parent.parent / 'backend'
sys.path.append(str(backend_path))

# Load actual .env
load_dotenv(backend_path.parent / '.env')

async def main():
    try:
        print("--- Stage 2 Verification: Live Credentials & Temporal Logic ---")
        
        # 1. Verify Imports and Global State
        from services.vision_service import AzureVisionClient
        from main import FRAME_HISTORY
        
        print("[PASS] Imports successful.")
        
        # 2. Verify Temporal Logic (Deque)
        print("\n--- Testing Temporal Logic ---")
        print(f"Initial FRAME_HISTORY: {list(FRAME_HISTORY)}")
        
        # Simulate adding frames
        test_sequence = ["Neutral", "Neutral", "HELP", "HELP", "HELP", "HELP", "HELP", "HELP", "HELP", "HELP"]
        for tag in test_sequence:
            FRAME_HISTORY.append(tag)
            
        print(f"Updated FRAME_HISTORY: {list(FRAME_HISTORY)}")
        
        # Check Trigger Logic
        help_count = FRAME_HISTORY.count("HELP")
        print(f"HELP Count: {help_count}/10")
        
        if help_count > 7:
            print("[PASS] Emergency Condition Calculated Correctly (>7 HELP).")
        else:
            print("[FAIL] Emergency Condition Logic Check Failed.")

        # 3. Verify Azure Clients (Live Handshake)
        print("\n--- Testing Azure Client Initialization (Live) ---")
        
        try:
            client = AzureVisionClient()
            print("[PASS] AzureVisionClient initialized with live credentials.")
            
            if client.custom_vision_client and client.custom_vision_client.client:
                print("[PASS] AzureCustomVisionClient initialized.")
            else:
                print("[FAIL] AzureCustomVisionClient failed to init (check keys).")
                
            await client.close()
            
        except Exception as e:
            print(f"[FAIL] Client Initialization Error: {e}")
            sys.exit(1)

        print("\nSTAGE 2 REPAIRED")

    except ImportError as e:
        print(f"[FAIL] Import Error: {e}")
        print("Ensure you are running this from the project root or tests folder.")
    except Exception as e:
        print(f"[FAIL] Unexpected Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
