import csv
import io


def tablify(array):
    rt = lambda row: "<td>" + "</td><td>".join(map(str, row)) + "</td>"
    return "<tr>" + "</tr><tr>".join(map(rt, array)) + "</tr>"


def csvify(array):
    sstream = io.StringIO()
    writer = csv.writer(sstream)
    for row in array:
        writer.writerow(row)
    return sstream.getvalue()


def surround_list(li, tag):
    pre = "<{}>".format(tag)
    post = "</{}>".format(tag)
    return pre + (post + pre).join(map(str, li)) + post
