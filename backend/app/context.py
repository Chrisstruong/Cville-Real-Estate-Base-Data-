from dataclasses import dataclass, field

from app.chat_context import ConversationContext
from app.map_actions import ShowStreetCrimesAction


@dataclass
class RequestContext:
    property_tool_calls: int = 0
    properties_returned: int = 0

    max_property_tool_calls: int = 1
    max_properties: int = 20

    street_tool_calls: int = 0
    pending_map_action: ShowStreetCrimesAction | None = None

    conversation: ConversationContext = field(
        default_factory=ConversationContext,
    )
    active_street_name: str | None = None
