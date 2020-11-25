import fret
from fret_mongo import FretMongo

mongo = FretMongo('mongodb://localhost:27017/')

fret.use(mongo)


@fret.command
def train(ws):
    rec = ws.recorder('train')

    rec.record(0.35, 'rmse-', model_size=4)
    rec.record(0.4, 'rmse-', model_size=3)
    rec.record(0.3, 'rmse-', model_size=5)


# then run: `fret summarize train -c metrics -r ws model_size -f .4f`
# you will see:
# metrics                   rmse
# ws          model_size
# ws/_default 3           0.3500
#             4           0.3500
#             5           0.3000
