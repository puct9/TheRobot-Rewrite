from ..routing import Pattern, RoutingList
from . import endpoints

PATTERNS = RoutingList(
    [
        Pattern(r"^\.vw j(?:oin)?$", endpoints.join_user),
        Pattern(r"^\.vw l(?:eave)?$", endpoints.leave_user),
        Pattern(r"^\.vw p(?:lay)? ([\w\-]+)$", endpoints.play_audio),
    ]
)
