import re

import fitz

import metadata as md


def find_page_range(pdf_path, statement_name):
    page_ranges = []
    doc = fitz.open(pdf_path)
    for i in range(len(doc)):
        page = doc[i]
        text = page.get_text().lower()
        if statement_name in text:
            metadata = md.generate_range(pdf_path, i + 1, i + 1)
            info = md.extract(metadata, ["font.size", "font.bold"])
            cells = []
            for inf in info:
                if len(inf["title"].strip()) > 1:
                    cells.append(
                        {
                            "title": inf["title"],
                            "size": float(inf["fields"]["font.size"]),
                        }
                    )
            count = {}
            for cell in cells:
                if cell["size"] in count:
                    count[cell["size"]] += 1
                else:
                    count[cell["size"]] = 1
            for cell in cells:
                if statement_name in cell["title"].lower().strip():
                    if count[cell["size"]] <= 2:
                        page_ranges.append((i + 1, i + 1))
                    break
    return page_ranges[0]


def find_unit(pdf_path, start):
    possible_units = [
        ["trillions", "trillion"],
        ["billions", "billion"],
        ["crores", "crore"],
        ["millions", "million"],
        ["lakhs", "lakh"],
        ["thousands", "thousand"],
    ]
    possible_numerical_units = [
        ["000000000000s", "'000000000000"],
        ["000000000s", "'000000000"],
        ["0000000s", "'0000000"],
        ["000000s", "'000000"],
        ["00000s", "'00000"],
        ["000s", "'000"],
    ]
    doc = fitz.open(pdf_path)
    page = doc[start - 1]
    text = page.get_text().lower()
    for units in possible_units:
        for unit in units:
            if unit in text:
                return units[0]
    for units in possible_numerical_units:
        for unit in units:
            if unit in text:
                return possible_units[possible_numerical_units.index(units)][0]


def find_column_positions(table):
    column_positions = []

    # Assuming there will always be 4 columns.
    columns = [[], [], [], []]

    skipped_rows = []
    for row in table:
        if len(row) == 4:
            for cell in row:
                columns[row.index(cell)].append([cell["left"], cell["right"]])
        elif len(row) < 4:
            skipped_rows.append(row)

    for row in skipped_rows:
        for cell in row:
            closest = None
            closest_diff = 10000
            for column in columns:
                curr_diff = abs(cell["left"] - column[0][0]) + abs(
                    cell["right"] - column[0][1]
                )
                if len(column) and curr_diff < closest_diff:
                    closest = column
                    closest_diff = curr_diff
            if closest_diff <= 100:
                closest.append([cell["left"], cell["right"]])

    for column in columns[::-1]:
        column.sort(key=lambda x: x[0])
        left_count = [[column[0][0], 1]]
        for cell in column[1:]:
            if cell[0] - left_count[-1][0] > 10:
                left_count.append([cell[0], 1])
            else:
                left_count[-1][1] += 1
        left_count.sort(key=lambda x: x[1], reverse=True)
        left = left_count[0][0]
        column.sort(key=lambda x: x[1])
        right = column[0][1]
        if len(column_positions):
            for cell in column[::-1]:
                if cell[1] > right and cell[1] < column_positions[-1]["left"]:
                    right = cell[1]
                    break
            for cell in columns[columns.index(column) + 1]:
                if cell[0] < column_positions[-1]["left"] and cell[0] > right:
                    column_positions[-1]["left"] = cell[0]
        else:
            right = column[-1][1]
        column_positions.append({"left": left - 10, "right": right})
    column_positions = column_positions[::-1]
    return column_positions


def find_statement_name(table):
    possible_statements = [
        "profit and loss",
        "balance sheet",
    ]
    for row in table:
        for cell in row:
            for statement in possible_statements:
                if statement in cell["title"].lower():
                    return statement


def find_max_cell_length(table):
    max_length = 0
    for row in table:
        for cell in row:
            if len(cell["title"]) > max_length:
                max_length = len(cell["title"])
    return max_length


def _is_first_row_match(row, column_positions):
    row_length = len(row)
    if row_length == 3:
        for i in range(3):
            if not (
                column_positions[i + 1]["left"]
                <= row[i]["left"]
                <= row[i]["right"]
                <= column_positions[i + 1]["right"]
            ):
                return False
    elif row_length == 4:
        for i in range(4):
            if not (
                column_positions[i]["left"]
                <= row[i]["left"]
                <= row[i]["right"]
                <= column_positions[i]["right"]
            ):
                return False
    else:
        return False
    return True


def _is_last_row_match(row, column_positions):
    row_length = len(row)
    if row_length == 3:
        if (
            abs(column_positions[0]["left"] - row[0]["left"]) > 50
            or abs(column_positions[2]["left"] - row[1]["left"]) > 50
            or abs(column_positions[3]["left"] - row[2]["left"]) > 50
        ):
            return False
    else:
        return False
    return True


def find_table_range(table, column_positions):
    table_range = []
    for row in table:
        if _is_first_row_match(row, column_positions):
            table_range.append(table.index(row))
            break
    for row in table[::-1]:
        if _is_last_row_match(row, column_positions):
            table_range.append(table.index(row))
            break
    return table_range


def find_first_row(table):
    for row in table:
        if (
            "assets" in row[0]["title"].lower()
            or "capital and liabilities" in row[0]["title"].lower()
            or "equity and liabilities" in row[0]["title"].lower()
            or "income" in row[0]["title"].lower()
        ):
            return table.index(row)


def find_column_names(rows):
    cells = []
    for row in rows:
        for cell in row:
            cells.append(cell)
    cells.sort(key=lambda x: x["left"])
    columns = [[cells[0]]]
    for cell in cells[1:]:
        if cell["right"] <= columns[-1][0]["right"]:
            columns[-1].append(cell)
        else:
            columns.append([cell])
    column_names = []
    for column in columns:
        column.sort(key=lambda x: x["top"])
        column_name = " ".join([cell["title"] for cell in column])
        column_names.append(column_name)
    if len(column_names) == 4:
        column_names.pop(0)
    column_names[0] = "Note"
    for i in range(1, 3):
        is_range = "-" in column_names[i]
        column_names[i] = re.findall(r"\b\d{4}\b", column_names[i])[0]
        if is_range:
            column_names[i] = str(int(column_names[i]) + 1)
    return column_names
