from fastapi import HTTPException

from app.chat_context import (
    ConversationContext,
    NeighborhoodMapContext,
    StreetMapContext,
)

from app.services.neighborhoods import load_neighborhoods
from app.services.streets import resolve_street_id


async def validate_conversation_context(
    conversation: ConversationContext,
) -> tuple[ConversationContext, str | None]:
    # Revalidate a serialized copy rather than trusting a mutable model.
    validated = ConversationContext.model_validate(conversation.model_dump())

    map_context = validated.map_context
    street_name = None

    if isinstance(map_context, StreetMapContext):
        street = await resolve_street_id(map_context.street_id)

        if street is None:
            raise HTTPException(
                status_code=422,
                detail=(
                    "The active street is no longer available. "
                    "Return to neighborhood view and select a street again."
                ),
            )

        street_name = street.name

    elif isinstance(map_context, NeighborhoodMapContext):
        if map_context.neighborhood_id not in load_neighborhoods():
            raise HTTPException(
                status_code=422,
                detail="The selected neighborhood is not available.",
            )

    return validated, street_name
