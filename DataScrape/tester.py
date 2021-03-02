# from functools import reduce
#
# def commenttreexml(comment, depth):
#     def transform(iicomment, iidepth):
#         separator = " "
#         base, indent = separator * iidepth, separator * iidepth + separator
#         root = "comment" if not iidepth else "reply"
#         attrs = iicomment.__dict__
#         replies = reduce(lambda a,b: a+b, [reply for reply in [""] + attrs.pop("replies")])
#         content = reduce(lambda a,b: a+b, [f"{indent}<{k}>{v}</{k}>\n" for k,v in zip(attrs.keys(), attrs.values())])
#         return f"{base}<{root}>\n" + content + replies + f"{base}</{root}>\n"
#     if len(comment.replies) == 0:
#         return transform(comment, depth)
#     else:
#         comment.replies = [commenttreexml(child, depth+1) for child in comment.replies]
#         return transform(comment, depth)
#

def extractinsights(comment):
    def isvaluable(cmt):
        value = False
        if cmt.body:
            value = True
        cmt.value = value


class CommentTypeA:
    def __init__(self, body, score, replies):
        self.body = body
        self.score = score
        self.replies = replies

    def evaluate(self):
        # traverse upside down tree
        def traversetree(comment, previous, deeper):
            # print(comment.body)
            comment.visited = True

            def analyse(cmt):
                cmt.valued = False
                if cmt.body == "f":
                    cmt.valued = True

            if deeper:
                analyse(comment)
                comment.parent = previous
                for reply in comment.replies:
                    reply.visited = False
            else:
                comment.valued |= previous.valued
                if not previous.valued:
                    comment.replies.remove(previous)

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


if __name__ == "__main__":
    commentf = CommentTypeA("f", 1, [])
    commente = CommentTypeA("e", 1, [commentf])
    commentd = CommentTypeA("d", 1, [])
    commentc = CommentTypeA("c", 1, [])
    commentb = CommentTypeA("b", 1, [commentd, commente])
    commenta = CommentTypeA("a", 1, [commentb, commentc])
    # serial_grades = pickle.dumps(commente)
    # received_grades = pickle.loads(serial_grades)

    # with open('my_json.txt', 'w') as fp:
    #     json.dump(commenta.__dict__, fp)

    commenta.evaluate()

    print(commenta)

    # comment = commenta
    #  while (True):
    #      for i in range(len(comment.replies)):
    #          tempreply = comment.replies[i]
    #          commenta.replies[i] = Comment(
    #              tempreply.body,
    #              tempreply.score,
    #              tempreply.replies,
    #          )

    # for comment in [commenta]:
    #     while (True):
    #         # empty comment
    #         cmt = Comment(
    #             comment.body,
    #             comment.score,
    #             [],
    #             len(comment.replies)
    #         )
    #
    #         depth += 1
    #         mydict[depth] = cmt
    #
    #         # if we have replies add them
    #         if (len(cmt.replies) < cmt.numreplies):#._comments):
    #             descendent = mydict[depth].pop()
    #             depth -= 1
    #
    #             print("SHALLOW", descendent.body)
    #         else:
    #             comment = comment.replies[len(comment.replies)]
    #
    #             print("DEEPER", cmt.body)
    #
    #         print(depth)
    #         if not depth:
    #             break

#
# import re
#
# def FormatTitle(searchstr):
#     pattern = r"\b(\w+day), (\w+) ([0-9]{2}), ([0-9]{4})"
#     match = re.search(pattern, searchstr)
#     weekday, month, day, year = match.groups()
#     return  f"{weekday} {day}-{month}-{year}"
#
#
# if __name__ == "__main__":
#     searchstr = "Weekend Thread for General Discussion and Plans for Saturday, February 06, 2021 and Sunday, February 07, 2021"
#     msg = FormatTitle(searchstr)
#     print(msg)
#
#     searchstr = "Daily Thread for General Trading and Plans for Thursday, February 04, 2021"
#     msg = FormatTitle(searchstr)
#     print(msg)
#
# def traverse():
#  print("HELLO")
#
# from functools import reduce
#
#
#
# if __name__ == "__main__":
#     a = {"a": 1}
#     b = {"b": 2}
#
#     big = {
#         0 : a,
#         1 : b
#     }
#
#     dictf = reduce(lambda x, y: dict((k, v + y[k]) for k, v in zip(x.keys(), x.values())), big.values())
