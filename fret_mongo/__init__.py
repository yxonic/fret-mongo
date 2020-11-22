import pymongo
import fret.common
from .summarizer import summarize


class FretMongo(fret.common.Plugin):
    commands = [summarize]

    def __init__(self, uri_or_client, db='fret'):
        if isinstance(uri_or_client, str):
            self.client = pymongo.MongoClient(uri_or_client)
        else:
            self.client = uri_or_client
        self.db = self.client[db]

    def apply(self, ws):
        def recorder(name):
            return Recorder(self.client.db[name])

        setattr(ws, 'recorder', recorder)


class Recorder:
    def __init__(self, collection):
        self.collection = collection

    def record(self, **kwargs):
        pass
