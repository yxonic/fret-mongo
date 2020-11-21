import pymongo
import fret.common


def summarize():
    pass


class FretMongo(fret.common.Plugin):
    commands = [summarize]

    def __init__(self, uri):
        self.client = pymongo.MongoClient()
