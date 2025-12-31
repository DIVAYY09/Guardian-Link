
import asyncio
import os
from services.brain_service import CrisisOrchestrator
from dotenv import load_dotenv

async def verify_brain():
    print("--- Verifying CrisisOrchestrator ---")
    
    # Load env (brain_service loads it too, but good to ensure)
    load_dotenv()
    
    try:
        orchestrator = CrisisOrchestrator()
        
        # Dummy data
        vision_context = "Person detected falling on the floor. Hand gesture 'HELP' identified with 98% confidence."
        user_metadata = {
            "user_id": "12345",
            "name": "Jane Doe",
            "location": "123 Main St, Springfield, IL (Lat: 39.78, Lon: -89.65)",
            "medical_history": "Hypertension"
        }
        
        print(f"Generating report for context: {vision_context}")
        print(f"Location: {user_metadata['location']}")
        
        report = await orchestrator.generate_dispatch_report(vision_context, user_metadata)
        
        print("\n=== GENERATED SBAR REPORT ===")
        print(report)
        print("=============================\n")
        
        if "CRITICAL ERROR" not in report:
            print("[PASS] Report generation successful.")
        else:
            print("[FAIL] Report generation returned error.")
            
    except ValueError as ve:
        print(f"[FAIL] Configuration Error: {ve}")
        print("Please ensure AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, and AZURE_OPENAI_DEPLOYMENT_NAME are set in .env")
    except Exception as e:
        print(f"[FAIL] Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(verify_brain())
