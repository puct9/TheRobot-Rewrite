from ..routing import Pattern, RoutingList
from . import endpoints

PATTERNS = RoutingList(
    [
        Pattern(
            r"^\.proxy e(?:mbed)?",
            endpoints.proxy_embed,
        )
    ]
)
