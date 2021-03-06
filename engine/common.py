import csv
import io


def readcsv(string):
    reader = csv.reader(string.split("\n"))
    return [list(map(lambda u:u.strip(), row)) for row in reader if row]


def csvify(array):
    sstream = io.StringIO()
    writer = csv.writer(sstream)
    for row in array:
        writer.writerow(row)
    return sstream.getvalue()


def surround_list(li, tag):
    pre = "<{}>".format(tag)
    post = "</{}>".format(tag)
    return "".join(pre + str(e) + post for e in li)


def tablify(array):
    rt = lambda row: "<td>" + "</td><td>".join(map(str, row)) + "</td>"
    return surround_list(map(rt, array), "tr")


def metapply(func, group):
    if isinstance(group, (list, tuple, set)):
        return group.__class__(metapply(func, element) for element in group)
    else:
        return func(group)


def dictrip(d, pattern):
    def gt(x):
        if x in d:
            return d[x]
        return ""
    return metapply(gt, pattern)


def forceints(n):
    def coerce(g):
        if not g:
            return 0
        try:
            return int(g)
        except ValueError:
            return 0
    return metapply(coerce, n)


def flatten(structure):
    g = []
    for x in structure:
        if isinstance(x, (list, tuple, set)):
            g += flatten(x)
        else:
            g.append(x)
    return g


def transpose(array):
    return [[array[x][y] for x in range(len(array))] for y in range(len(array[0]))]
