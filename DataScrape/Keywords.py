import re

KWORDS_DICT = {
    "🚀": 10,
    "🌕": 8,
    "buy": 1,
    "profit": 1,
    "risky": -1,
    "punt": 1,
    "the dip": 15,
    "winner": 3,
    "multi bagger": 10,
    "sleeping on": 5,
    "distruptive": 3,
    "potential": 2,
    "look at": 2,
    "are primed": 5,
    "sleepig on": 10
}

DD_DICT = {
    "undervalued": 1,
    "goal price": 1
}

# I THINK RE.COMPILE IS HASHABLE?!

# HOW TO COME UP WITH THE WEIGHTS?
SENTIMENT_DICT = {
    re.compile("🚀"): (10, "HYPE"),
    re.compile("🌕"): (10, "HYPE"),
    re.compile("to the mo+n"): (10, "HYPE"),
    re.compile("multi[- ]bagger"): (8, "HYPE"),
    re.compile("let'?s go+"): (10, "HYPE"),
    re.compile("tendies"): (8, "HYPE"),
    re.compile("profit"): (8, "HYPE"),
    re.compile("good run"): (10, "HYPE"),
    re.compile("winner"): (8, "HYPE"),
    re.compile("are primed"): (8, "HYPE"),
    re.compile("distruptive"): (8, "HYPE"),
    re.compile("exciting"): (10, "HYPE"),

    # buyers, sellers?

    re.compile("buy the dip"): (15, "TIP"),  # not buy.. not waiting to...re.compile("dyor"): (10, "TIP"),
    re.compile("not a.* advisor"): (12, "TIP"),
    re.compile("goal price"): (10, "TIP"),
    re.compile("\$[0-9.]* by"): (10, "TIP"),
    re.compile("under[- ]valued"): (10, "TIP"),
    re.compile("sleeping on"): (8, "TIP"),
    re.compile("slept on"): (8, "TIP"),
    re.compile("look at"): (5, "TIP"),
    re.compile("potential"): (5, "TIP"),

    re.compile("risky"): (-10, "GAMBLE"),
    re.compile("wild ?card"): (-5, "GAMBLE"),
    re.compile("punt"): (0, "GAMBLE"),

    re.compile("up \%[0-9.]*"): (10, "GAIN")
    # apes emoji
}

if __name__ == "__main__":
    search = " TO THE MOON "
    total = 0
    for k, w in SENTIMENT_DICT.items():
        match = k.search(search.lower())
        if match:  # .group()
            print(match.group())
            total += w
    print(total)
