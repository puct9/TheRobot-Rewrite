from ..routing import Pattern, RoutingList
from . import endpoints

PATTERNS = RoutingList(
    [
        Pattern(
            r"^\.counter (.+) (\+|\-)$",
            endpoints.edit_counter,
        ),
    ]
)
