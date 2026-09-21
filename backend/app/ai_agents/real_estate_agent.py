from agents import Agent, ModelSettings

from app.context import RequestContext
from app.tools.property_tools import get_largest_properties

real_estate_agent = Agent[RequestContext](
    name="Charlottesville Real Estate Assistant",
    instructions="""
    You are a helpful real estate assistant for Charlottesville property data.

    PROPERTY RESULT POLICY:
    - Return at most 20 properties per user request.
    - Never split oversized requests into multiple batches.
    - If a request exceeds the limit, explain the cap briefly.
    - Keep responses concise.
    - For property lists, only include the fields needed to answer the user's question.
    """,
    tools=[
        get_largest_properties,
    ],
    model_settings=ModelSettings(
        max_tokens=500,
    ),
)
