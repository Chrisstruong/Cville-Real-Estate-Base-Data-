from agents import Runner

from app.context import RequestContext
from app.ai_agents.real_estate_agent import real_estate_agent


async def run_real_estate_agent(message: str) -> str:
    request_context = RequestContext()

    result = await Runner.run(
        real_estate_agent,
        message,
        context=request_context,
    )

    # return the agent's final response
    return result.final_output
