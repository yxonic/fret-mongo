import pymongo
import fret.common


def summarize():
    pass


class FretMongo(fret.common.Plugin):
    commands = [summarize]

    def __init__(self, uri_or_client):
        if isinstance(uri_or_client, str):
            self.client = pymongo.MongoClient(uri_or_client)
        else:
            self.client = uri_or_client
