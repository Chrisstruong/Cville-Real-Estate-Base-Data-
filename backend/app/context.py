from dataclasses import dataclass


@dataclass
class RequestContext:
    property_tool_calls: int = 0
    properties_returned: int = 0

    max_property_tool_calls: int = 1
    max_properties: int = 20
