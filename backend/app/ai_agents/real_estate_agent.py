from agents import Agent

from app.context import RequestContext
from app.tools.property_tools import get_largest_properties

real_estate_agent = Agent[RequestContext](
    name="Charlottesville Real Estate Assistant",
    instructions="""
    You are a helpful real estate assistant for Charlottesville property data.

Use the available tools when answering questions about properties.

Never request more than 20 properties from a single tool call.
    """,
    tools=[
        get_largest_properties,
    ],
)
