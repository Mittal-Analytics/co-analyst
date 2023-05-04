import json
import os
import re

import explorer
import grading as gr
import metadata as md
import separator
import unifier


def _find_column_positions(table):
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


def _find_statement_name(table):
    possible_statements = [
        "profit and loss",
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
        raise FileNotFoundError(f"File not found at {pdf_path}.")

    try:
        start, end = kwargs["start"], kwargs["end"]
    except KeyError:
        try:
            statement_name = kwargs["statement_name"].lower()
            start, end = explorer.find_page_range(pdf_path, statement_name)
        except KeyError:
            raise KeyError("Either start and end or statement_name must be provided.")

    unit = explorer.find_unit(pdf_path, start)
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
                "left": float(inf["fields"]["bbox.left"]),
                "right": float(inf["fields"]["bbox.right"]),
                "top": float(inf["fields"]["bbox.top"]),
            }
        )
    cells.sort(key=lambda cell: cell["top"])

    pages = []
    row = []
    for cell in cells:
        if len(row) == 0 or row[0]["top"] - cell["top"] < 1:
            row.append(cell)
        else:
            pages.append(sorted(row, key=lambda x: x["left"]))
            row = [cell]
    pages = separator.separate_if_two(pages)

    response = []
    for table in pages:
        column_positions = _find_column_positions(table)
        table = unifier.unite_separated_cells(table, column_positions)

        for row in table:
            for cell in row:
                cell["title"] = _sanitize(cell)

        statement_name = _find_statement_name(table)

        max_right = column_positions[1]["left"] - (
            column_positions[2]["left"] - column_positions[1]["left"] * 3 / 2
        )
        unifier.sanitize_line_break(table, _find_max_length(table), max_right)

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
