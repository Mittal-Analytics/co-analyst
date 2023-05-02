import json
import os
import re

import fitz

import grading as gr
import metadata as md


def _find_page_range(pdf_path, statement_name):
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
            sizes = {}
            for cell in cells:
                if cell["size"] in sizes:
                    sizes[cell["size"]] += 1
                else:
                    sizes[cell["size"]] = 1
            for cell in cells:
                if statement_name in cell["title"].lower().strip():
                    if sizes[cell["size"]] <= 2:
                        page_ranges.append((i + 1, i + 1))
                    break
    return page_ranges[0]


def _find_unit(pdf_path, start):
    possible_units = [
        ["trillions", "trillion"],
        ["billions", "billion"],
        ["crores", "crore"],
        ["millions", "million"],
        ["lakhs", "lakh"],
        ["thousands", "thousand"],
    ]
    possible_numerical_units = [
        "000000000000s",
        "000000000s",
        "0000000s",
        "000000s",
        "00000s",
        "000s",
        "'000000000000",
        "'000000000",
        "'0000000",
        "'000000",
        "'00000",
        "'000",
    ]
    doc = fitz.open(pdf_path)
    page = doc[start - 1]
    text = page.get_text().lower()
    for units in possible_units:
        for unit in units:
            if unit in text:
                return units[0]
    for unit in possible_numerical_units:
        if unit in text:
            return possible_units[possible_numerical_units.index(unit) % 6][0]


def _find_separation_point(table):
    lefts = []
    for row in table:
        for cell in row[1:]:
            lefts.append(cell["left"])
    lefts.sort()
    left_count = [[lefts[0], 1]]
    for left in lefts[1:]:
        if left != left_count[-1][0]:
            left_count.append([left, 1])
        else:
            left_count[-1][1] += 1
    left_count.sort(key=lambda x: x[1], reverse=True)
    if left_count[0][1] > 25:
        return left_count[0][0] - 10
    return None


def _separate_cells(row, separation_point):
    separated_cells = [[], []]
    for cell in row:
        if cell["left"] < separation_point:
            separated_cells[0].append(cell)
        else:
            separated_cells[1].append(cell)
    return separated_cells


def _separate_if_two(table):
    separation_point = _find_separation_point(table)
    if separation_point == None:
        return [table]
    separated_tables = [[], []]
    for row in table:
        separated_cells = _separate_cells(row, separation_point)
        if len(separated_cells[0]) > 0:
            separated_tables[0].append(separated_cells[0])
        if len(separated_cells[1]) > 0:
            separated_tables[1].append(separated_cells[1])
    return separated_tables


def _find_column_positions(table):
    column_positions = []

    # Assuming there will always be 4 columns.
    columns = [[], [], [], []]

    first_row_index = None
    last_row_index = None
    skipped_rows = []
    for row in table:
        if len(row) == 4:
            if first_row_index == None:
                first_row_index = table.index(row)
            last_row_index = table.index(row)
            for cell in row:
                if cell["right"] == 1097:
                    print(cell["title"])
                columns[row.index(cell)].append([cell["left"], cell["right"]])
        else:
            skipped_rows.append(row)

    for row in skipped_rows:
        if table.index(row) < first_row_index:
            continue
        elif table.index(row) > last_row_index:
            break

        while len(row) > 4:
            row[0]["title"] += row[1]["title"]
            row[0]["right"] = row[1]["right"]
            row.pop(1)

        for cell in row:
            closest = None
            closest_diff = 10000
            for column in columns:
                if len(column) and abs(cell["left"] - column[0][0]) < closest_diff:
                    closest = column
                    closest_diff = abs(cell["left"] - column[0][0])
            if (
                closest
                and closest_diff <= 100
                and not cell["right"] > max(closest, key=lambda x: x[1])[1]
            ):
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
        column_positions.append({"left": left, "right": right})
    column_positions = column_positions[::-1]
    return column_positions


def _unite_separated_cells(table, column_positions):
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


def _find_statement_name(table):
    possible_statements = [
        "profit and loss",
        "cash flow",
        "balance sheet",
    ]
    for row in table:
        for cell in row:
            for statement in possible_statements:
                if statement in cell["title"].lower():
                    return statement


def _sanitize(cell):
    # Remove all commas for numerical values otherwise all dots.
    if re.match(r"^\d{1,3}(,\d{3})*(\.\d+)?|\d+(\.\d+)?$", cell["title"]):
        return cell["title"].replace(",", "").strip()
    return cell["title"].rstrip(".").strip()


def _find_max_length(table):
    max_length = 0
    for row in table:
        for cell in row:
            if len(cell["title"]) > max_length:
                max_length = len(cell["title"])
    return max_length


def _merge_rows(table, row1, row2):
    row1[0]["title"] += " " + row2[0]["title"]
    if len(row1) == 1:
        for cell in row2[1:]:
            row1.append(cell)
    table.remove(row2)


def _sanitize_line_break(table, max_length, max_right, index=0):
    if index == len(table) - 1:
        return table
    if (
        table[index][0]["right"] >= max_right
        and len(table[index][0]["title"]) >= max_length - 5
    ):
        if len(table[index]) == 1 or len(table[index + 1]) == 1:
            _merge_rows(table, table[index], table[index + 1])
    return _sanitize_line_break(table, max_length, max_right, index + 1)


def _is_first_row_match(row, column_positions):
    row_length = len(row)
    if row_length == 3:
        for i in range(3):
            if abs(column_positions[i + 1]["left"] - row[i]["left"]) > 50:
                return False
    elif row_length == 4:
        for i in range(4):
            if abs(column_positions[i]["left"] - row[i]["left"]) > 50:
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


def _find_table_range(table, column_positions):
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


def _find_first_row(table):
    for row in table:
        if (
            "assets" in row[0]["title"].lower()
            or "capital and liabilities" in row[0]["title"].lower()
            or "equity and liabilities" in row[0]["title"].lower()
            or "income" in row[0]["title"].lower()
        ):
            return table.index(row)


def _find_column_names(rows):
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


def _remove_list_marker(title):
    pattern = r"^[\dA-Za-z]+\.\s|\([^\)]*\)\s|\s*[-*•]+(?=\s)"
    return re.sub(pattern, "", title).strip()


def _n(title):
    if title[0] == "(" and title[-1] == ")":
        return f"-{title[1:-1]}"
    return title


def _extract_data_from_table(statement_name, table, grading, column_names, unit):
    stack = [{"title": statement_name, "unit": unit, "data": []}]
    for row in table:
        try:
            while (
                len(stack) > 1
                and grading[row[0]["title"]] >= grading[stack[-1]["title"]]
            ):
                stack[-1]["title"] = _remove_list_marker(stack[-1]["title"])
                stack[-2]["data"].append(stack[-1])
                stack.pop()
        except KeyError:
            if len(row) == 2:
                stack[-1]["title"] = _remove_list_marker(stack[-1]["title"])
                stack[-2]["data"].append(stack[-1])
                stack.pop()
        stack.append({"title": row[0]["title"], "data": []})
        if len(row) == 2:
            stack[-1]["title"] = stack[-2]["title"]
            stack[-1]["data"].append(
                {
                    column_names[1]: _n(_remove_list_marker(row[0]["title"])),
                    column_names[2]: _n(_remove_list_marker(row[1]["title"])),
                }
            )
        elif len(row) == 3:
            stack[-1]["data"].append(
                {
                    column_names[1]: _n(_remove_list_marker(row[1]["title"])),
                    column_names[2]: _n(_remove_list_marker(row[2]["title"])),
                }
            )
        elif len(row) == 4:
            stack[-1]["data"].append(
                {
                    column_names[0]: _remove_list_marker(row[1]["title"]),
                    column_names[1]: _n(_remove_list_marker(row[2]["title"])),
                    column_names[2]: _n(_remove_list_marker(row[3]["title"])),
                }
            )

    while len(stack) > 1:
        stack[-1]["title"] = _remove_list_marker(stack[-1]["title"])
        stack[-2]["data"].append(stack[-1])
        stack.pop()

    return stack[0]


def extract_data_from_pdf(pdf_path, **kwargs):
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"File not found at {pdf_path}")

    try:
        start, end = kwargs["start"], kwargs["end"]
    except KeyError:
        try:
            statement_name = kwargs["statement_name"].lower()
            start, end = _find_page_range(pdf_path, statement_name)
        except KeyError:
            raise KeyError("Either start and end or statement_name must be provided")

    unit = _find_unit(pdf_path, start)
    metadata = md.generate_range(pdf_path, start, end)
    info = md.extract(
        metadata,
        [
            "font.size",
            "font.color",
            "font.bold",
            "bbox.left",
            "bbox.right",
            "bbox.top",
        ],
    )

    cells = []
    for inf in info:
        cells.append(
            {
                "title": inf["title"],
                "size": float(inf["fields"]["font.size"]),
                "color": inf["fields"]["font.color"],
                "bold": True if inf["fields"]["font.bold"] == "true" else False,
                "left": round(float(inf["fields"]["bbox.left"])),
                "right": round(float(inf["fields"]["bbox.right"])),
                "top": round(float(inf["fields"]["bbox.top"])),
            }
        )
    cells.sort(key=lambda x: x["top"])

    tables = []
    row = []
    for cell in cells:
        if len(row) == 0 or cell["top"] - row[0]["top"] < 5:
            row.append(cell)
        else:
            tables.append(sorted(row, key=lambda x: x["left"]))
            row = [cell]

    tables = _separate_if_two(tables)

    response = []
    for table in tables:
        column_positions = _find_column_positions(table)
        table = _unite_separated_cells(table, column_positions)

        for row in table:
            for cell in row:
                cell["title"] = _sanitize(cell)

        statement_name = _find_statement_name(table)

        max_right = column_positions[1]["left"] - (
            column_positions[2]["left"] - column_positions[1]["left"] * 3 / 2
        )
        _sanitize_line_break(table, _find_max_length(table), max_right)

        start, end = _find_table_range(table, column_positions)
        table = table[start : end + 1]

        first_row = _find_first_row(table)
        column_names = _find_column_names(table[0:first_row])
        table = table[first_row:]

        grading = gr.make_grading(table)
        data = _extract_data_from_table(
            statement_name, table, grading, column_names, unit
        )

        if data["title"] == None:
            response[-1]["data"].append(data["data"][0])
        else:
            response.append(data)
    return json.dumps(response)
