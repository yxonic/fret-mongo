import pymongo
import fret.common
from .summarizer import get_summarize_command


class FretMongo(fret.common.Plugin):
    def __init__(self, uri_or_client, db='fret'):
        if isinstance(uri_or_client, str):
            self.client = pymongo.MongoClient(uri_or_client)
        else:
            self.client = uri_or_client
        self.db = self.client[db]
        self.commands.append(get_summarize_command(self.db))

    def apply(self, ws):
        def recorder(name):
            return Recorder(ws, self.db[name])

        setattr(ws, 'recorder', recorder)


class Recorder:
    def __init__(self, ws, collection):
        self.ws = ws
        self.collection = collection

    def record(self, value, metrics, descending=None, **kwargs):
        is_des = descending is True or \
            (descending is None and metrics.endswith('-'))
        metrics = metrics.rstrip('+-') + ('-' if is_des else '+')

        data = {}
        for name, cfg in self.ws.config_dict().items():
            for k, v in cfg.items():
                data[name + ':' + k] = v

        data.update({'metrics': metrics, 'value': value})
        data.update(kwargs)

        data['ws'] = str(self.ws)

        self.collection.insert_one(data)
