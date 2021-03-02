import numpy as np


def avgPrice(df):
    return df.Close.add(df.Low.add(df.High)) / 3


def vwap(df):
    def vvwap(df):
        p = avgPrice(df).values
        q = df.Volume.values
        cumQty = q.cumsum()
        return df.assign(vwap=(p * q).cumsum() / np.where(cumQty == 0, np.nan, cumQty))

    df = df.groupby(df.index.date, group_keys=False).apply(vvwap)
    return df.pop('vwap')
