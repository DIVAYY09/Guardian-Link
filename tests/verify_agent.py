import asyncio
import sys
import os
import pytest

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from agent_protocol import GuardianMasterAgent

@pytest.mark.asyncio
async def test_high_alert_keyword():
    agent = GuardianMasterAgent()
    
    # Mock input with keyword
    input_data = {
        "captions": [{"text": "Smoke detected in the hallway", "confidence": 0.99}],
        "objects": [],
        "gestures": []
    }
    
    result = await agent.perceive_environment(input_data)
    
    assert result["alert_status"] == "HIGH_ALERT"
    assert "Keyword detected" in result["alert_reason"]
    print("Keyword Alert Test Passed")

@pytest.mark.asyncio
async def test_gesture_sequence():
    agent = GuardianMasterAgent()
    
    # Mock data with HELP gesture
    help_frame = {"gestures": [{"tag": "HELP", "probability": 0.9}]}
    empty_frame = {"gestures": []}
    
    import copy
    
    # 1. First HELP - No alert yet (need 3/5)
    res1 = await agent.perceive_environment(copy.deepcopy(help_frame))
    assert res1["alert_status"] == "NORMAL"
    
    # 2. Second HELP
    res2 = await agent.perceive_environment(copy.deepcopy(help_frame))
    assert res2["alert_status"] == "NORMAL"
    
    # 3. Empty
    res3 = await agent.perceive_environment(copy.deepcopy(empty_frame))
    assert res3["alert_status"] == "NORMAL"
    
    # 4. Third HELP within 5 frames -> High Alert? NO, len < 5 yet.
    res4 = await agent.perceive_environment(copy.deepcopy(help_frame))
    assert res4["alert_status"] == "NORMAL" # Still accumulating
    
    # 5. Fourth HELP (Length 5) -> High Alert
    res5 = await agent.perceive_environment(copy.deepcopy(help_frame))
    assert res5["alert_status"] == "HIGH_ALERT"
    assert "Consistent 'HELP' signal" in res5["alert_reason"]
    print("Gesture Sequence Test Passed")

if __name__ == "__main__":
    # Manually run async tests if pytest not invoked directly
    # (Though we installed pytest, so we could use it, but manual run is robust)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(test_high_alert_keyword())
        loop.run_until_complete(test_gesture_sequence())
        print("All Agent Logic Tests Passed!")
    finally:
        loop.close()
