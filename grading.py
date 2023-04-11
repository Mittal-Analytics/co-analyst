import re


def _find_sizes(table):
    sizes = []
    for row in table:
        sizes.append(row[0]["size"])
    final = []
    tmp = set(sizes)
    for i in range(len(tmp)):
        count = sizes.count(sizes[0])
        final.append((sizes[0], count))
        while count:
            sizes.remove(sizes[0])
            count -= 1
    final.sort(key=lambda x: x[1], reverse=True)
    return final


def _point_size(size, sizes):
    for i in range(len(sizes)):
        if size == sizes[i][0]:
            return i + 50
    return -5


def _find_colors(table):
    colors = []
    for row in table:
        colors.append(row[0]["color"])
    final = []
    tmp = set(colors)
    for i in range(len(tmp)):
        count = colors.count(colors[0])
        final.append((colors[0], count))
        while count:
            colors.remove(colors[0])
            count -= 1
    final.sort(key=lambda x: x[1], reverse=True)
    return final


def _point_color(color, colors):
    for i in range(len(colors)):
        if color == colors[i][0]:
            return i + 100
    return -5


def _point_bold(bold):
    if bold:
        return 10
    return -5


def _point_all_caps(title):
    if title.isupper():
        return 20
    return -5


def _point_has_no_number(title):
    if title.replace(".", "").isnumeric():
        return -5
    return 5


def _point_has_no_list_marker(title):
    pattern = r"^[\dA-Za-z]+\.\s|\([^\)]*\)\s|\s*[-*•]+\s*"
    if re.match(pattern, title):
        return -5
    return 10


# TODO: Add support for giving point for front margin.
def make_grading(table):
    grading = {}
    sizes = _find_sizes(table)
    colors = _find_colors(table)
    # We do not need the most common size and color.
    sizes.pop(0)
    colors.pop(0)
    for row in table:
        if re.match(r"^\d{1,3}(,\d{3})*(\.\d+)?|\d+(\.\d+)?$", row[0]["title"]):
            continue
        grading[row[0]["title"]] = _point_size(row[0]["size"], sizes)
        grading[row[0]["title"]] += _point_color(row[0]["color"], colors)
        grading[row[0]["title"]] += _point_bold(row[0]["bold"])
        grading[row[0]["title"]] += _point_all_caps(row[0]["title"])
        grading[row[0]["title"]] += _point_has_no_number(row[0]["title"])
        grading[row[0]["title"]] += _point_has_no_list_marker(row[0]["title"])

    grading = {k: v for k, v in sorted(grading.items(), key=lambda item: item[1])}
    return grading