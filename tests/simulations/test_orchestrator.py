import asyncio
import json
import sys
import os

# Add backend to sys.path to import GuardianMasterAgent
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend')))
from agent_protocol import GuardianMasterAgent

async def run_simulation():
    # Load scenarios
    with open('tests/simulations/emergency_gestures.json', 'r') as f:
        scenarios = json.load(f)

    agent = GuardianMasterAgent()

    print(f"Loaded {len(scenarios)} scenarios for testing.\n")

    for i, scenario in enumerate(scenarios):
        print(f"--- Scenario {i+1}: {scenario['scenario']} ---")
        await agent.run_mission(image_input=scenario)
        print("\n")

if __name__ == "__main__":
    asyncio.run(run_simulation())
