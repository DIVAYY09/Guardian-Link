
import asyncio
import os
from services.brain_service import CrisisOrchestrator
from dotenv import load_dotenv

async def verify_agentic_loop():
    print("--- Verifying Agentic Loop ---")
    load_dotenv()
    
    try:
        orchestrator = CrisisOrchestrator()
        
        # Load User Profile (Mocking main.py behavior)
        import json
        try:
            with open("backend/user_profile.json", "r") as f:
                user_metadata = json.load(f)
        except FileNotFoundError:
            # Fallback if running from proper cwd or if file missing
             try:
                with open("user_profile.json", "r") as f:
                    user_metadata = json.load(f)
             except:
                print("Warning: user_profile.json not found in CWD. Using mock.")
                user_metadata = {"location": "Test Lab", "user_id": "test_user", "name": "Test User", "medical_history": "None"}

        # Ensure location is set for test
        user_metadata["location"] = "Test Lab (Mock)"
        
        # Test Case 1: High Severity, Valid
        print("\n[TEST 1] High Severity (Fire + Help)")
        vision_context_1 = "A room filled with thick black smoke and flames visible in the corner."
        sign_detected_1 = "HELP"
        
        result1 = await orchestrator.run_agentic_loop(vision_context_1, sign_detected_1, user_metadata)
        print(f"Result 1: Status={result1['status']}, Severity={result1.get('severity')}, Speech={result1.get('speech_triggered')}")
        
        # Test Case 2: Inconsistent (Context Mismatch)
        # Note: Our prompt instructions are lenient for safety ("prioritize visual"), but let's see if we can trigger a mismatch warning
        # or at least see the validation log.
        print("\n[TEST 2] Potential Mismatch (Peaceful Park + Help)")
        vision_context_2 = "A peaceful sunny park with children playing. No danger visible."
        sign_detected_2 = "HELP" # Might be valid (hidden danger), but let's see validation output
        
        result2 = await orchestrator.run_agentic_loop(vision_context_2, sign_detected_2, user_metadata)
        print(f"Result 2: Status={result2['status']}, Severity={result2.get('severity')}")

    except Exception as e:
        print(f"[FAIL] Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(verify_agentic_loop())
