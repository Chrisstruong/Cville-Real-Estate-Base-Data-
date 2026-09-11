import asyncio
from agents import Runner, set_default_openai_key

from app.ai_agents.real_estate_agent import real_estate_agent
from app.database.connection import pool
from app.config import settings

set_default_openai_key(settings.openai_api_key)

async def main():
    await pool.open()
    
    try:
        results = await Runner.run(
            real_estate_agent,
            "What are the 5 largest tax-exempt properties?",
        )
        # final_output comes from the object returned by Runner.run(...) in the openAI SDK
        print(results.final_output) # Return the agent's response text after it finishes reasoning and calling any tools it needs
    
    finally:
        await pool.close()
        
if __name__ == "__main__":
    asyncio.run(
        main(),
        loop_factory=asyncio.SelectorEventLoop
    )