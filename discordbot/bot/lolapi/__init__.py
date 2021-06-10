from ..routing import Pattern, RoutingList
from . import endpoints

PATTERNS = RoutingList(
    [
        Pattern(
            r"^\.lol m(?:astery)? ([a-zA-Z]{2,4}) (.{1,16})$",
            endpoints.lol_masteries,
        ),
        Pattern(
            r"^\.lol p(?:rofile)? ([a-zA-Z]{2,4}) (.{1,16})$",
            endpoints.lol_profile,
        ),
    ]
)
