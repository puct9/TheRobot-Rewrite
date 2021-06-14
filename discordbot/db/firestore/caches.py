import asyncio
from copy import deepcopy
from typing import Any, Dict, List, Optional, Set

from google.cloud.firestore import (
    Client,
    CollectionReference,
    DocumentReference,
    DocumentSnapshot,
)


class DocumentCache:
    """
    Cache for a single document by implementing a snapshot listener. It is
    recommended by Google to avoid too many snapshot listeners.
    """

    def __init__(
        self,
        document_ref_sync: DocumentReference,
    ) -> None:
        self.ref_sync = document_ref_sync
        self.client = Client()
        self._data: Dict[str, Any] = {}
        # Nothing to gain from loading lazily
        self.watch = self.ref_sync.on_snapshot(self.on_snapshot)

    def __del__(self) -> None:
        self.watch.unsubscribe()

    async def get_dict(self) -> Optional[Dict[str, Any]]:
        # Make this a coroutine for consistency
        return deepcopy(self._data)

    def on_snapshot(
        self, doc_snapshot: DocumentSnapshot, changes: Any, read_time: Any
    ):
        # For some reasaon `doc_snapshot` can be a list [doc_snapshot]
        if isinstance(doc_snapshot, list):
            doc_snapshot = doc_snapshot[0]
        self._data = doc_snapshot.to_dict()


class IndexCache:
    """
    Cache for Firestore clients, automatically maintaining a list of document
    ids under a collection in an efficient manner by implementing a snapshot
    listener. It is recommended by Google to avoid too many snapshot listeners.
    This does not maintain a record of the actual data stored in the documents
    to reduce memory cost.
    """

    def __init__(
        self,
        collection_ref_sync: CollectionReference,
    ) -> None:
        # Do not update immediately - load lazily
        # If we are never called, we can potentially avoid many reads
        # If we are called and there are few documents, we don't use many reads
        # either
        self.ref_sync = collection_ref_sync
        self.client = Client()
        self.loaded = False
        self._index: Set[str] = set()

    def __del__(self) -> None:
        # Not sure if required but literally nothing to lose from this
        if hasattr(self, "watch"):
            self.watch.unsubscribe()

    async def get_document_ids(self) -> List[str]:
        if self.loaded:
            return list(self._index)
        # Start listening for updates
        self.start_watch()
        # Wait for the first on_snapshot call to complete. The first call will
        # contain all documents.
        while not self.loaded:
            await asyncio.sleep(0.1)
        return list(self._index)

    def on_snapshot(
        self, col_snapshot: Any, changes: Any, read_time: Any
    ) -> None:
        for change in changes:
            if change.type.name == "ADDED":
                self._index.add(change.document.id)
            if change.type.name == "REMOVED":
                try:
                    self._index.remove(change.document.id)
                except KeyError:
                    pass
        self.loaded = True

    def start_watch(self) -> None:
        self.watch = self.ref_sync.on_snapshot(self.on_snapshot)
