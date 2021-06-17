from google.cloud.language import Document, LanguageServiceAsyncClient

from ..bases import BaseService


class GCPService(BaseService):
    def __init__(self) -> None:
        self.client = LanguageServiceAsyncClient()

    async def sentiment_analysis(self, text: str) -> float:
        doc = Document(content=text, type_=Document.Type.PLAIN_TEXT)
        res = (
            await self.client.analyze_sentiment(request={"document": doc})
        ).document_sentiment
        return res.score * res.magnitude
