import datetime as dt
import os
import shutil
import sys
from functools import reduce
from pathlib import Path
from time import strptime

import pandas as pd
import praw
from pytz import timezone

sys.path.append('..')

from DataScrape.Keywords import SENTIMENT_DICT
from _devconfig import USER, PASSWORD, CLIENT_SECRET, CLIENT_ID
import re

# TODO : UPDATE TICKERS LEDGER
#        ORDER BY UP?DOWN
#       alternate hype, tips
#       make sentiment analysis proper


# https://www.reddit.com/wiki/search
# Crystal Ball Gazing
# List superstars

# u/jakekustardmustard

# /u/calculated-punt


# GO OVER INDIVIDUAL REPLIES, CATEGORISE AS
# TIP
#


# RE.COMPILE kword
# create a legder for sentiment... get imormation on volume, volatility

# TODO: to _deconfig.py
CSV_BASE = "C:/Users/liamd/Documents/Project/AlgoTrading/DataScrape/Symbols/"
DAILY_BASE = "C:/Users/liamd/Documents/Project/AlgoTrading/DataScrape/Dailies/"

ASX_LISTING_BASE = r"C:\Users\liamd\Documents\Project\AlgoTrading\DataScrape\ASX Listings"
ASX_LISTING = ASX_LISTING_BASE + "\\" + os.listdir(ASX_LISTING_BASE)[-1]

SEPARATOR = " "


class Submission():
    def __init__(self, title, commentforest, created_date):  # , **kwargs):
        self.title = title
        self.commentforest = commentforest
        self.sourced = dt.datetime.now()
        self.created_date = created_date
        # self.__dict__ = {**self.__dict__, **kwargs}

    def extractTitleDate(self):
        """When was this created"""
        pattern = r"\b(\w+day), (\w+) ([0-9]{2}), ([0-9]{4})"
        match = re.search(pattern, self.title)
        weekday, month, day, year = match.groups()
        month_num = strptime(month, "%B").tm_mon
        return f"{year}-{month_num:02d}-{day} {weekday}"

    def extractInsights(self):

        for comment in self.commentforest:
            comment.evaluate()

        # Flatten
        all_comments = []
        comment_queue = sub.commentforest[:]  # Seed with top-level
        while comment_queue:
            comment = comment_queue.pop(0)

            all_comments.append(comment)
            comment_queue.extend(comment.replies)

        # Sentiment for tickers, and sentiment per comment/reply
        sentiment_tickers = {}  # Key: CODE, Val: num, {} KEY; "TIP", weighting
        sentiment_categories = {}  # Key: "TIP", Val: Comment, Weighting
        for comment in all_comments:
            for mention in set(comment.mentions):
                if mention not in sentiment_tickers:
                    sentiment_tickers[mention] = (1, {})
                else:
                    occurrences, sentimentdict = sentiment_tickers[mention]
                    sentiment_tickers[mention] = (occurrences + 1, sentimentdict)

            if comment.valued:
                for cat, weight in comment.score.items():
                    if cat not in sentiment_categories:
                        sentiment_categories[cat] = [(comment, weight)]
                    else:
                        sentiment_categories[cat].append((comment, weight))

                    for mention in set(comment.mentions):
                        occurrences, existing = sentiment_tickers[mention]
                        if not cat in existing:
                            existing[cat] = weight
                        else:
                            existing[cat] += weight
                        sentiment_tickers[mention] = occurrences, existing

        # sentiment = {}
        # for comment in self.commentforest:
        #     if comment.valued:
        #
        #         all_comments = []
        #         comment_queue = [comment]  # Seed with top-level
        #         while comment_queue:
        #             comment = comment_queue.pop(0)
        #             all_comments.append(comment)
        #             comment_queue.extend(comment.replies)
        #
        #         # GET THE MAX Score for each
        #
        #         for cat, weight in comment.score.items():
        #             if cat not in sentiment:
        #                 sentiment[cat] = [(comment, weight)]
        #             else:
        #                 sentiment[cat].append((comment, weight))
        #

        # Sort tickers by mention, sort categories by best weighted
        sentiment_tickers = {k: v for k, v in
                             sorted(sentiment_tickers.items(), key=lambda items: items[1][0], reverse=True)}
        for key in sentiment_categories.keys():
            sentiment_categories[key].sort(key=lambda x: x[-1], reverse=True)

        # Save metrics
        try:
            netmatches = 0
            nethype = 0
            nettips = 0
            for code, (nummatches, sentiment) in list(sentiment_tickers.items()):
                netmatches += nummatches
                nethype += sentiment['HYPE'] if "HYPE" in sentiment else 0
                nettips += sentiment['TIP'] if "TIP" in sentiment else 0

            if not nethype:
                nethype = 1
            if not nettips:
                nettips = 1

            asx_listings = pd.read_csv(ASX_LISTING, index_col=0).code.values

            for code in set(list(sentiment_tickers.keys()) + list(asx_listings)):
                if code in sentiment_tickers.keys():
                    nummatches, sentiment = sentiment_tickers[code]
                    ntips = sentiment['TIP'] if 'TIP' in sentiment else 0
                    nhype = sentiment['HYPE'] if 'HYPE' in sentiment else 0

                    df = pd.DataFrame({"mentions": nummatches,
                                       "mentions_perc": 100 * nummatches / netmatches,
                                       "tips": ntips,
                                       "tips_perc": 100 * ntips / nettips,
                                       "nhype": nhype,
                                       "hype_perc": 100 * nhype / nethype}, index=[self.created_date])
                    df.index = pd.DatetimeIndex(df.index)
                else:
                    df = pd.DataFrame({"mentions": 0,
                                       "mentions_perc": 0,
                                       "tips": 0,
                                       "tips_perc": 0,
                                       "nhype": 0,
                                       "hype_perc": 0}, index=[self.created_date])
                    df.index = pd.DatetimeIndex(df.index)

                csv_path = CSV_BASE + f'{code}.csv'
                record_exists = Path(csv_path).exists()
                if record_exists:
                    df_load = pd.read_csv(csv_path, index_col=0)  # , mode='a', header=False, index=False)
                    df_load.index = pd.DatetimeIndex(df_load.index)
                    before = df_load[:self.created_date]
                    after = df_load[self.created_date:]
                    df = pd.concat([before[before.index != df.index[0]], df, after[after.index != df.index[0]]])
                df.to_csv(csv_path, index=True)
        except Exception as e:
            print("WRITEOUT F", e)

        # # Save metrics
        # try:
        #     mypath = f'C:/Users/liamd/Documents/Project/AlgoTrading/DataScrape/Symbols/'
        #     onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
        #     for file in onlyfiles:
        #         filename = basename(file)
        #         extension = splitext(filename)[1]
        #         if not extension == "csv":
        #             continue
        #
        #
        # except Exception as e:
        #     print("WRITEOUT F", e)
        #     pass

        # Add discussed xml
        discussed_xml = ""
        to_mention = 5
        discussed_xml += SEPARATOR + "<discussed>\n"
        try:
            for code, (nummatches, sentiment) in list(sentiment_tickers.items())[
                                                 :min(to_mention, len(sentiment_tickers))]:
                try:
                    sentiment_str = reduce(lambda a, b: a + b,
                                           [f"{k}={v}" if i + 1 == len(sentiment) else f"{k}={v}, " for i, (k, v) in
                                            enumerate(sentiment.items())])
                except:
                    sentiment_str = ""
                discussed_xml += SEPARATOR * 2 + f"<mention>{code} ({nummatches}) {sentiment_str}</mention>\n"  # >:(
        except Exception as e:
            print("disuss fail", e)
        discussed_xml += SEPARATOR + "</discussed>\n"

        # authors = []
        rockets = []
        for comment in all_comments:
            if comment.valued:
                if re.search("[Rr]ocket (\w+ )?[Aa]nalysis", comment.body):
                    rockets.append(comment)

        highlighted = []
        rocket_xml = ""
        if len(rockets):
            rocket_xml += SEPARATOR + "<rockets>\n"
            for rocket in rockets:
                rocket_xml += rocket.toXml(startdepth=2, brief=True, insight=True)
                highlighted.append((rocket.author, rocket.created_utc))
            rocket_xml += SEPARATOR + "</rockets>\n"

        tip_xml_internal = ""
        try:
            to_tip = 5
            for comment, weight in sentiment_categories['TIP']:
                while comment.parent != None:
                    comment = comment.parent
                if (comment.author, comment.created_utc) in highlighted:
                    continue
                tip_xml_internal += comment.toXml(startdepth=2, brief=True, insight=True)
                to_tip -= 1
                highlighted.append((comment.author, comment.created_utc))

                if not to_tip:
                    break
        except Exception as e:
            print('TIP FAILED', e)
        finally:
            if tip_xml_internal == "":
                tip_xml = ""
            else:
                tip_xml = f"{SEPARATOR}<tip>\n" + tip_xml_internal + f"{SEPARATOR}</tip>\n"

        hype_xml_internal = ""
        try:
            to_hype = 5
            for comment, weight in sentiment_categories['HYPE']:
                while comment.parent != None:
                    comment = comment.parent
                if (comment.author, comment.created_utc) in highlighted:
                    continue
                hype_xml_internal += comment.toXml(startdepth=2, brief=True, insight=True)
                to_hype -= 1
                highlighted.append((comment.author, comment.created_utc))

                if not to_hype:
                    break
        except Exception as e:
            print('HYPE FAILED', e)
        finally:
            if hype_xml_internal == "":
                hype_xml = ""
            else:
                hype_xml = f"{SEPARATOR}<hype>\n" + hype_xml_internal + f"{SEPARATOR}</hype>\n"

        return discussed_xml + rocket_xml + tip_xml + hype_xml

    def subToXml(self):
        head = '<?xml version="1.0" encoding="UTF-8"?>\n'

        # highlights
        highlightforest = self.extractInsights()
        highlights = "<highlights>\n" + highlightforest + "</highlights>\n"

        # Comments
        commentforest = reduce(lambda a, b: a + b,
                               [comment.toXml(startdepth=1, brief=True) for comment in self.commentforest])
        comments = "<Comments>\n" + commentforest + "</Comments>\n"

        # Put it all together
        self.xml = head + f'<root date="{self.extractTitleDate()}">\n' + highlights + "&#10;" * 2 + "\n" + comments + "</root>\n"
        return self.xml

    def writeout(self):
        date = self.extractTitleDate()
        xml = self.subToXml()

        f = open(DAILY_BASE + f"Daily Thread {date}.xml", "w", encoding='utf-8')
        f.write(xml)
        f.close()

        f = open('C:/Users/liamd/OneDrive/Quantitative Trading/xml scrapes/' + f"Daily Thread {date}.xml", "w",
                 encoding='utf-8')
        f.write(xml)
        f.close()


class Comment:
    def __init__(self, body=None, ups=None, downs=None, replies=[], author=None, author_flair=None, created_utc=None,
                 total_awards_received=None,
                 top_awarded_type=None, edited=None, is_root=None, is_submitter=None, gilded=None):
        self.body = body
        self.ups = ups
        self.downs = downs
        self.replies = replies
        self.author = author
        self.author_flair = author_flair
        self.created_utc = created_utc
        self.total_awards_received = total_awards_received
        self.top_awarded_type = top_awarded_type
        self.edited = edited
        self.is_root = is_root
        self.is_submitter = is_submitter
        self.gilded = gilded

    def toXml(self, startdepth=0, brief=False, insight=False):
        """Transform a Comment object to an xml representation"""
        dict = self.__dict__.copy()

        def commenttreexml(comment, depth=0, brief=False, insight=False):
            def transform(iicomment, iidepth):
                base, indent = SEPARATOR * iidepth, SEPARATOR * iidepth + SEPARATOR
                root = "comment" if not (iidepth - startdepth) else "reply"  # CARE START DPETH
                attrs = iicomment.__dict__

                if insight and "valued" in attrs:
                    if not attrs["valued"]:
                        return ""
                root_add = ""
                try:
                    ups = attrs.pop("ups")
                    downs = attrs.pop("downs")
                    author = attrs.pop("author")
                    root_add += f' ups="{ups}" downs="{downs}" author="{author}"'

                    created_time = timezone('utc').localize(dt.datetime.utcfromtimestamp(attrs.pop("created_utc")))
                    created_time = created_time.astimezone(timezone('Australia/Brisbane'))
                    root_add += f' created="{created_time}"'

                    if insight:
                        sentiment, weight = max(attrs["score"].items(), key=lambda i: i[-1])
                        root_add += f' sentiment="{sentiment} {weight}"'
                except Exception as e:
                    pass

                try:
                    attrs["body"] = re.sub("&", "&amp;", attrs["body"])
                    attrs["body"] = re.sub("<", "&lt;", attrs["body"])
                    attrs["body"] = re.sub(">", "&gt;", attrs["body"])
                except:
                    pass

                # Preserve replies
                replies = reduce(lambda a, b: a + b, [reply for reply in [""] + attrs.pop("replies")])

                # Which fields are wanted in the markup
                if not brief:
                    tokeep = ["body", "author_flair", "total_awards_received"]
                else:
                    tokeep = ["body"]
                try:
                    content = reduce(lambda a, b: a + b, [f"{indent}<{k}>{v}</{k}>\n" for k, v in attrs.items() if
                                                          (v is not None) and (k in tokeep)])
                except Exception as e:
                    content = ""
                return f"{base}<{root + root_add}>\n" + content + replies + f"{base}</{root}>\n"

            if len(comment.replies) == 0:
                return transform(comment, depth)
            else:
                comment.replies = [child.toXml(startdepth=depth + 1, brief=brief, insight=insight) for child in
                                   comment.replies]
                return transform(comment, depth)

        xml = commenttreexml(self, depth=startdepth, brief=brief, insight=insight)
        self.__dict__ = dict
        return xml

    def evaluate(self):
        """Perform sentiment analysis on a comment"""

        # traverse upside down tree
        def traversetree(comment, previous, deeper):
            comment.visited = True

            def analyse(cmt):
                asx_listings = pd.read_csv(ASX_LISTING, index_col=0)
                listings = asx_listings.code.values
                baddies = ["CAN", "AND", "FOR", "ALL", "ARE", "HAS", 'BUY', 'MAN', 'ONE', 'COS', 'ADD', 'NEW',
                           'TIP', 'OIL', "GAS", "CAP", "ATH", "ATM", "UBI", "GOLD", "BIT", "RED"]

                # Set matched tickers
                cmt.valued = False
                cmt.mentions = []
                if cmt.body is not None:
                    matches = re.findall(r"\b\w{3,6}\b", cmt.body)
                    for match in matches:
                        if (match in listings or (
                                match.upper() in listings and match.upper() not in baddies)) and match.upper() != "ASX":
                            cmt.mentions.append(match.upper())

                    for k, (w, reason) in SENTIMENT_DICT.items():
                        if k.search(cmt.body.lower()):  # .group()
                            if not reason in cmt.score:
                                cmt.score[reason] = w
                            else:
                                cmt.score[reason] += w
                    cmt.valued = True if (len(cmt.score) + len(matches)) > 0 else False

            if deeper:
                comment.score = {}
                analyse(comment)
                comment.parent = previous
                for reply in comment.replies:
                    reply.visited = False
            else:
                comment.valued |= previous.valued

            # If we are not climbing, it is the first time we have visited the node
            # If there are no replies
            numreplies = len(comment.replies)
            visited_replies = sum([reply.visited for reply in comment.replies])

            # If there are unvisited rpleis
            if (numreplies - visited_replies):
                return traversetree(comment.replies[visited_replies], comment, True)
            else:
                if comment.parent == None:
                    return
                else:
                    return traversetree(comment.parent, comment, False)

        # comment, previous, deeper
        traversetree(self, None, True)

    @staticmethod
    def commenttree(redditcomment):
        """Transform from PRAW to comment object"""

        def transform(cmt):
            try:
                author = cmt.author.name
            except:
                author = "DELETED"
            try:
                return Comment(
                    body=cmt.body,
                    ups=cmt.ups,
                    downs=cmt.downs,
                    replies=cmt.replies._comments,
                    author=author,
                    author_flair=cmt.author_flair_text,
                    created_utc=cmt.created_utc,
                    total_awards_received=cmt.gilded if (cmt.total_awards_received) else None,
                    top_awarded_type=cmt.top_awarded_type,
                    edited=cmt.edited if (cmt.edited) else None,
                    is_submitter=cmt.is_submitter if (cmt.is_submitter) else None,
                    gilded=cmt.gilded if (cmt.gilded) else None,
                )
            except Exception as e:
                return Comment()

        redditcomment = transform(redditcomment)

        if len(redditcomment.replies) == 0:
            return redditcomment
        else:
            redditcomment.replies = [Comment.commenttree(child) for child in redditcomment.replies]
            return redditcomment


if __name__ == "__main__":
    reddit = praw.Reddit(client_id=CLIENT_ID, \
                         client_secret=CLIENT_SECRET, \
                         user_agent='asxbets_scraper', \
                         username=USER, \
                         password=PASSWORD)
    subreddit = reddit.subreddit('ASX_Bets')

    # query -> the query to search for
    # sort -> relevance, hot, top, new, comments
    # time_filter -> all, day, hour, month, week, year

    # Crystal Ball
    # DD
    # Top of the week ?

    listinggenerator = subreddit.search(
        query='flair:"Daily Thread"',
        sort='new',
        limit=2
    )

    submissions = list(listinggenerator)
    submissions.reverse()

    for i, submission in enumerate(submissions):
        print(f"Starting submissions ({i + 1}/{len(submissions)})")
        if submission.title.find("Premarket") > -1:
            try:
                created_time = timezone('utc').localize(dt.datetime.utcfromtimestamp(submission.created_utc))
                created_time = created_time.astimezone(timezone('Australia/Brisbane'))

                submission.comment_sort = "top"
                commentroots = []
                for comment in submission.comments.list():
                    try:
                        if comment.is_root and comment.body != 'DELETED' and comment.author != 'AutoModerator':
                            commentroots.append(comment)
                    except:
                        pass

                sub = Submission(
                    title=submission.title,
                    commentforest=[Comment.commenttree(comment) for comment in commentroots],
                    created_date=created_time)

                sub.writeout()
            except Exception as e:
                print(f"{i} failed: {e}")

    src_files = os.listdir(DAILY_BASE)
    for file_name in src_files:
        full_file_name = os.path.join(DAILY_BASE, file_name)
        if os.path.isfile(full_file_name):
            shutil.copy(full_file_name, r"C:\Users\liamd\OneDrive\Quantitative Trading\xml scrapes")

    src_files = os.listdir(CSV_BASE)
    for file_name in src_files:
        full_file_name = os.path.join(CSV_BASE, file_name)
        if os.path.isfile(full_file_name):
            shutil.copy(full_file_name, r"C:\Users\liamd\OneDrive\Quantitative Trading\xml scrapes\Symbols")
