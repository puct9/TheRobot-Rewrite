from ..routing import Pattern, RoutingList
from . import endpoints

PATTERNS = RoutingList(
    [Pattern(r"\.ai (?:iv3|inceptionv3)?", endpoints.inception_v3_inference)]
)
