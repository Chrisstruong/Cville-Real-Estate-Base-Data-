from agents import Agent

from app.tools.property_tools import get_largest_properties

real_estate_agent = Agent(
    name="Charlottesville Real Estate Assistant",
    instructions="""
    You are an assitant for the Charlottesville real-estate database.
    
    Use the provided tools whenver the user asks about property data.
    
    Do not invent property information.
    
    Keep answers clear and concise.
    """,
    tools=[
        get_largest_properties,
    ],
    
)