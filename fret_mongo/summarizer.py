import pandas as pd
from collections.abc import Iterable
from fret import argspec


def collect(collection, regex=None, last=False):
    summarizer = Summarizer()
    filter = {}
    if regex is not None:
        filter['ws'] = {'$regex': regex}
    if last:
        docs = list(collection.aggregate(
            [
                {'$sort': {'ws': 1, 'date': 1}},
                {
                    '$group':
                    {
                        '_id': '$ws',
                        'id': {'$last': '$_id'}
                    }
                }
            ]
        ))
        ids = [doc['id'] for doc in docs]
        filter['_id'] = {'$in': ids}
    for data in collection.find(filter):
        data.add(**data)
    return summarizer


class Summarizer:
    def __init__(self, data=None):
        self.data = data or []
        self.is_des = dict()

    def __len__(self):
        return len(self.data)

    def add(self, value, metrics, **kwargs):
        _metrics = metrics.rstrip('+-')
        self.is_des[_metrics] = metrics.endswith('-')
        data = dict(metrics=_metrics, value=value)
        data.update(kwargs)
        self.data.append(data)

    def df(self):
        return pd.DataFrame(self.data)

    def summarize(self, rows=None, columns=None, row_order=None,
                  column_order=None, scheme='best', topk=-1, filter=None):
        df = self.df()
        if filter is not None:
            df = filter(df)
        df = df.fillna('-')
        if rows is None and columns is None:
            columns = ['metrics']
        if rows is None or columns is None:
            current = set(rows or columns)
            current.add('value')
            groups = [c for c in df.columns if c not in current]
            if rows is None:
                rows = groups
            else:
                columns = groups
        groups = rows + columns
        df = df.groupby(groups)['value']
        ind = groups.index('metrics')

        if isinstance(scheme, str) or not isinstance(scheme, Iterable):
            scheme = [scheme]

        def f(x):
            if topk > 0:
                x = x.sort_values(
                    ascending=self.is_des.get(x.name[ind])
                )[:topk]
            for s in scheme:
                if s == 'best':
                    x = x.min() if self.is_des.get(x.name[ind]) else x.max()
                elif s == 'mean':
                    x = x.mean()
                elif callable(s):
                    x = s(x)
                else:
                    raise ValueError('scheme not supported')
            return x

        df = df.apply(f)
        df = df.unstack(columns)
        if row_order is not None:
            if isinstance(row_order[0], list):
                df = df.reindex(
                    pd.MultiIndex.from_product(row_order,
                                               names=df.rows.names),
                    axis=0
                )
            else:
                df = df.reindex(row_order, axis=0)
        if column_order is not None:
            if isinstance(column_order[0], list):
                df = df.reindex(
                    pd.MultiIndex.from_product(column_order,
                                               names=df.columns.names),
                    axis=1
                )
            else:
                df = df.reindex(column_order, axis=1)
        return df


def get_summarize_command(db):
    def summarize(
        collection=argspec(help='collection name', required=True),
        rows=argspec(
            help='row names',
            nargs='+', default=None
        ),
        columns=argspec(
            help='column names',
            nargs='*', default=None
        ),
        row_selection=argspec(
            help='selection of row headers, different headers separated '
                 'by _ (eg: -rs H1 H2 _ h1 h2)',
            nargs='+', default=None
        ),
        column_selection=argspec(
            help='selection of column headers, different headers '
                 'separated by _ (eg: -rs C1 C2 _ c1 c2)',
            nargs='+', default=None
        ),
        scheme=('best', 'output scheme',
                ['best', 'mean', 'mean_with_error']),
        topk=(-1, 'if >0, best k results will be taken into account'),
        regex=(None, 'regex to filter workspace'),
        format=(None, 'float point format spec (eg: .4f)'),
        output=(None, 'output format', ['html', 'latex']),
        last=(False, 'only retrieve last record in each result directory')
    ):
        """Command ``summarize``.
        Summarize all results recorded by ``ws.record``.
        """
        summarizer = collect(db[collection], regex, last)
        if len(summarizer) == 0:
            raise ValueError('no results found')

        row_order = row_selection and _selection_to_order(row_selection)
        column_order = column_selection and \
            _selection_to_order(column_selection)

        schemes = []
        if scheme == 'mean_with_error':
            schemes.append(lambda x: (x.mean(), x.std()))
            spec = ':' + format if format else ''
            fmt = r'{%s}$\pm${%s}' % (spec, spec) if output == 'latex' \
                else '{%s}±{%s}' % (spec, spec)
            schemes.append(lambda x: fmt.format(*x))
        else:
            schemes.append(scheme)
            if format:
                fmt = '{:%s}' % format
                schemes.append(lambda x: fmt.format(x))
        df = summarizer.summarize(rows, columns, row_order, column_order,
                                  scheme=schemes, topk=topk)
        if output == 'latex':
            return df.to_latex(escape=False)
        if output == 'html':
            return df.to_html(escape=False)
        return df

    return summarize


def _selection_to_order(selection):
    order = []
    lo = 0
    while True:
        # noinspection PyUnresolvedReferences
        try:
            hi = selection.index('_', lo)
        except ValueError:
            # no _ left
            order.append(selection[lo:])
            break
        order.append(selection[lo:hi])
        lo = hi + 1
    if len(order) == 1:
        order = order[0]
    return order
