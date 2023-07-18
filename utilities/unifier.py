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


def _merge_rows(table, i1, i2):
    row1 = table[i1]
    row2 = table[i2]
    row1_length = len(row1)
    for i in range(row1_length):
        if row1[i]["title"] and row2[i]["title"]:
            row1[i]["title"] += "\n" + row2[i]["title"]
    table.pop(i2)


def unite_separated_rows(table, column_positions):
    # TODO: Complete this.
    return table
