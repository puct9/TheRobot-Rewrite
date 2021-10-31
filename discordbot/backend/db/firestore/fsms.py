from typing import Any, Callable
from google.cloud.firestore import CollectionReference

from .dtypes import Message


class FirestoreMessagingService:
    """
    Listens to a collection for additions and sends them as message by
    implementing a snapshot listener. It is recommended by Google to avoid too
    many snapshot listeners.
    """

    def __init__(
        self,
        collection_ref_sync: CollectionReference,
        callback: Callable[[str, Any], None],
    ) -> None:
        self.ref_sync = collection_ref_sync
        self.callback = callback
        self.watch = self.ref_sync.on_snapshot(self.on_snapshot)

    def __del__(self) -> None:
        self.watch.unsubscribe()

    def on_snapshot(
        self, col_snapshot: Any, changes: Any, read_time: Any
    ) -> None:
        for change in changes:
            if change.type.name == "ADDED":
                message = Message(change.document.to_dict())
                self.callback(
                    "message",
                    {
                        "target": message.target,
                        "content": message.content,
                    },
                )
                # Delete the document as we are done with it
                change.document.reference.delete()
