import datetime as dt
import json
import os
import re
from html import unescape

import pandas as pd

from DataScrape.DownloadUtil import download


def get_latest():
    base = r"C:\Users\liamd\Documents\Project\AlgoTrading\DataScrape\ASX Listings"
    src_files = os.listdir(base)
    src_files.sort(reverse=True)
    return base + "\\" + src_files[0]


if __name__ == "__main__":
    webpage = "https://www.marketindex.com.au/asx-listed-companies"
    contents = download(url=webpage, lying=True)
    table = unescape(re.search('<asx-listed-companies-table :companies=".*"></asx-listed-companies-table>', contents,
                               re.DOTALL).group())
    sections = re.findall('{(.+?),"formatted":.+?}}', table)

    df = pd.DataFrame(json.loads("{" + sections[0][0:] + "}"), index=[0])
    for section in sections[1:]:
        df = df.append(json.loads("{" + section[0:] + "}"), ignore_index=True)
    df.to_csv(f'ASX Listings/ASX_LISTINGS {dt.datetime.now().date()}.csv', index=False)
