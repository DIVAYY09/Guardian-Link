
import asyncio
import sys
import os
import json
from pathlib import Path

# Add backend to path to allow imports
backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.append(str(backend_path))

from services.brain_service import CrisisOrchestrator
from dotenv import load_dotenv

# Load env from backend/.env or root .env
load_dotenv(backend_path.parent / ".env")

async def test_brain_sbar():
    print("--- Testing CrisisOrchestrator SBAR Generation ---")
    
    # Check Env
    if not os.getenv("GEMINI_API_KEY"):
         print("[SKIP] GEMINI_API_KEY not found. Skipping live LLM test.")
         return

    try:
        orchestrator = CrisisOrchestrator()
        
        # Mock Input
        sign_detected = "HELP - CHOKING"
        vision_context = "User is clutching throat in a kitchen. Face turning red. Distress visible."
        
        # Load User Metadata
        profile_path = backend_path / "user_profile.json"
        if profile_path.exists():
            with open(profile_path, "r") as f:
                user_metadata = json.load(f)
        else:
            print("[WARN] user_profile.json not found, using valid mock.")
            user_metadata = {
                "name": "Sarah Connor", 
                "medical_history": "Asthmatic, Severe Peanut Allergy", 
                "emergency_contact": "John Connor",
                "location": "Mock Location"
            }
            
        print(f"Input Context: {vision_context}")
        print(f"Input Sign: {sign_detected}")
        print(f"User Medical History: {user_metadata.get('medical_history')}")
        
        # Run through Agentic Loop (which calls generate_dispatch_report)
        result = await orchestrator.run_agentic_loop(vision_context, sign_detected, user_metadata)
        
        if result["status"] != "COMPLETED":
            print(f"[FAIL] Agentic Loop did not complete. Status: {result['status']}, Reason: {result.get('reason')}")
            return

        sbar_report = result["sbar_report"]
        
        print("\n=== GENERATED SBAR REPORT ===")
        print(sbar_report)
        print("=============================\n")
        
        # Verifications
        # 1. Professionalism (Heuristic: Check for SBAR keywords)
        sbar_keywords = ["SITUATION", "BACKGROUND", "ASSESSMENT", "RECOMMENDATION"]
        missing_kw = [kw for kw in sbar_keywords if kw not in sbar_report.upper()]
        
        if not missing_kw:
             print("[PASS] SBAR Structure detected.")
        else:
             print(f"[FAIL] Missing SBAR keywords: {missing_kw}")

        # 2. Medical Metadata
        if user_metadata["name"] in sbar_report and ("Peanut Allergy" in sbar_report or "Asthmatic" in sbar_report or "medical history" in sbar_report.lower()):
            print("[PASS] Medical Metadata included.")
        else:
            print("[WARN] Medical Metadata might be missing or rephrased.")

        # 3. Word Count (< 100 words)
        word_count = len(sbar_report.split())
        print(f"Word Count: {word_count}")
        if word_count < 100:
            print("[PASS] Report is under 100 words.")
        else:
            print(f"[FAIL] Report is too long ({word_count} words). Should be < 100.")

    except Exception as e:
        print(f"[FAIL] Exception during test: {e}")

if __name__ == "__main__":
    asyncio.run(test_brain_sbar())
