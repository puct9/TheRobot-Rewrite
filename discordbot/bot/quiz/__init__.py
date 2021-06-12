from ..routing import Pattern, RoutingList
from . import endpoints

PATTERNS = RoutingList(
    [
        Pattern(
            r"^\.quiz ([^\s]+)$",
            endpoints.quiz_subject_random,
        )
    ]
)
