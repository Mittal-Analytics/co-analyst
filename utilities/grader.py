from . import tools


# Find all the different values of a property in the table.
def _find_property_values(table, property):
    tmp = []
    res = {}
    for row in table:
        tmp.append(row[0][property])
        if row[0][property] in res:
            res[row[0][property]] += 1
        else:
            res[row[0][property]] = 1
    res = list(res.items())
    res.sort(key=lambda x: (x[1], tmp.index(x[0])), reverse=True)
    return res


def _point_size(size, sizes):
    # Negative points for having the most common size.
    if sizes:
        sizes.pop(0)
    for i in range(len(sizes)):
        if size == sizes[i][0]:
            return i + 50
    return -5


def _point_color(color, colors):
    # Negative points for the having the most common color.
    if colors:
        colors.pop(0)
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
    if tools.has_list_marker(title):
        return -5
    return 10


def _point_has_front_margin(left):
    return int(left)


def get_grading(table):
    grading = {}
    sizes = _find_property_values(table, "size")
    colors = _find_property_values(table, "color")
    for row in table:
        for cell in row:
            grading[cell["title"]] = (
                _point_size(cell["size"], sizes)
                + _point_color(cell["color"], colors)
                + _point_bold(cell["bold"])
                + _point_all_caps(cell["title"])
                + _point_has_no_number(cell["title"])
                + _point_has_no_list_marker(cell["title"])
                - _point_has_front_margin(cell["left"])
            )

    grading = {k: v for k, v in sorted(grading.items(), key=lambda item: item[1])}
    return grading
