from utilities import tools


def unite_separated_list_markers(table):
    for row in table:
        row_length = len(row)
        if row_length > 1:
            i = 0
            while i < row_length - 1 and i < 1:
                if tools.contain_only_list_marker(row[i]["title"]):
                    row[i]["title"] += " " + row[i + 1]["title"]
                    row[i]["right"] = row[i + 1]["right"]
                    row.pop(i + 1)
                    break
                else:
                    i += 1
    return table


def unite_separated_cells(table, column_positions):
    for row in table:
        row_length = len(row)
        if row_length > 1:
            i = 0
            while i < row_length - 1 and i < 3:
                if row[i]["title"].strip() == "":
                    row.pop(i)
                    row_length -= 1
                elif row[i + 1]["left"] < column_positions[i + 1]["left"]:
                    row[i]["title"] += " " + row[i + 1]["title"]
                    row[i]["right"] = row[i + 1]["right"]
                    row.pop(i + 1)
                    row_length -= 1
                else:
                    i += 1
    return table


def _merge_rows(table, row1, row2):
    row1[0]["title"] += " " + row2[0]["title"]
    if len(row1) == 1:
        for cell in row2[1:]:
            row1.append(cell)
    table.remove(row2)


def unite_separated_rows(table, max_length, max_right, index=0):
    if index == len(table) - 1:
        return table
    if (
        table[index][0]["right"] >= max_right
        and len(table[index][0]["title"]) >= max_length - 5
    ):
        if len(table[index]) == 1 or len(table[index + 1]) == 1:
            _merge_rows(table, table[index], table[index + 1])
    return unite_separated_rows(table, max_length, max_right, index + 1)
