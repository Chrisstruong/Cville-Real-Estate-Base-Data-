from collections.abc import AsyncIterator

from agents import Runner
from openai.types.responses import ResponseTextDeltaEvent

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
    usage = result.context_wrapper.usage

    print("\n===== AGENT USAGE ======")
    print("LLM requests:", usage.requests)
    print("Input tokens:", usage.input_tokens)
    print("Output tokens:", usage.output_tokens)
    print("Total token:", usage.total_tokens)
    print("\n==========\n")
    return result.final_output


async def stream_real_estate_agent(message: str) -> AsyncIterator[str]:
    request_context = RequestContext()

    result = Runner.run_streamed(
        real_estate_agent,
        message,
        context=request_context,
    )

    async for event in result.stream_events():
        if event.type == "raw_response_event" and isinstance(
            event.data, ResponseTextDeltaEvent
        ):
            yield event.data.delta

    usage = result.context_wrapper.usage

    print("\n===== STREAMING AGENT USAGE ======")
    print("LLM requests:", usage.requests)
    print("Input tokens:", usage.input_tokens)
    print("Output tokens:", usage.output_tokens)
    print("Total tokens:", usage.total_tokens)
    print("==================================\n")
