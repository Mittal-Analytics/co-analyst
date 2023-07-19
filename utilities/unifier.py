from utilities import grader

from . import tools


def _merge_cells(row, i1, i2):
    row[i1]["title"] += " " + row[i2]["title"]
    row[i1]["right"] = row[i2]["right"]
    row.pop(i2)


def unite_separated_list_markers(table):
    for row in table:
        row_length = len(row)
        i = 0
        while i < row_length - 1 and i < 1:
            if (
                tools.contain_only_list_marker(row[i]["title"])
                and row[i + 1]["left"] - row[i]["right"]
                < 50  # TODO: Eradicate magic number.
            ):
                _merge_cells(row, i, i + 1)
                break
            else:
                i += 1


def _are_other_cells_empty(row):
    content_count = 0
    for cell in row:
        if cell["title"]:
            content_count += 1
    return content_count == 1


def _is_content_same_level(table, i1, i2, j):
    grading = grader.get_grading([table[i1], table[i2]])
    return (
        abs(grading[table[i1][j]["title"]] - grading[table[i2][j]["title"]])
        < 10  # TODO: Eradicate magic number.
    )


def _merge_rows(table, i1, i2):
    row1 = table[i1]
    row2 = table[i2]
    row1_length = len(row1)
    for i in range(row1_length):
        if row1[i]["title"] and row2[i]["title"]:
            row1[i]["title"] += "\n" + row2[i]["title"]
        elif row2[i]["title"]:
            row1[i]["title"] = row2[i]["title"]
    table.pop(i2)


def unite_separated_rows(table, column_positions):
    table_length = len(table)
    i = 0
    while i < table_length - 1:
        row = table[i]
        row_length = len(row)
        for j in range(row_length):
            cell = row[j]
            if cell["title"] == "":
                continue
            if (
                column_positions[j]["right"] - cell["right"]
                < 10  # TODO: Eradicate magic number.
            ):
                if _are_other_cells_empty(row) and _is_content_same_level(
                    table, i, i + 1, j
                ):
                    _merge_rows(table, i, i + 1)
                    table_length -= 1
                    i -= 1
                    break
        i += 1
    return table
