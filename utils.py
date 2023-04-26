import os
import fitz
import re
import metadata as md
import grading as gr
import json


def _find_page_range(pdf_path, statement_name):
    if statement_name == "balance sheet":
        keywords = [
            "balance sheet",
            "assets",
            "cash",
            "bank",
            "fixed assets",
            "liabilities",
            "capital",
            "equity",
            "total",
        ]
    doc = fitz.open(pdf_path)
    for page in doc:
        matched_keywords = 0
        text = page.get_text()
        for keyword in keywords:
            if keyword in text.lower():
                matched_keywords += 1
        if matched_keywords >= 8:
            # +1 because index starts from 0.
            return page.number + 1, page.number + 1


def _find_unit(pdf_path, start, end):
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
            return possible_units[possible_numerical_units.index(unit)][0]


def _find_separation_point(table):
    lefts = []
    for row in table:
        for cell in row[1:]:
            lefts.append(cell["left"])
    lefts.sort()
    left_count = [[lefts[0], 1]]
    for left in lefts[1:]:
        if left - left_count[-1][0] > 50:
            left_count.append([left, 1])
        else:
            left_count[-1][1] += 1
    left_count.sort(key=lambda x: x[1], reverse=True)
    if left_count[0][1] > 32:
        return left_count[0][0]
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
    for i in range(4):
        lefts = []
        for row in table:
            if len(row) == 4:
                lefts.append(row[i]["left"])
        if i == 0:
            column_positions.append({"left": min(lefts)})
        else:
            lefts.sort()
            tmp = [[lefts[0], 1]]
            for left in lefts[1:]:
                if left - tmp[-1][0] > 10:
                    tmp.append([left, 1])
                else:
                    tmp[-1][1] += 1
            tmp.sort(key=lambda x: x[1], reverse=True)
            left = tmp[0][0]
            column_positions.append({"left": left})
    diff = column_positions[3]["left"] - column_positions[2]["left"]
    if column_positions[1]["left"] < column_positions[2]["left"] - diff:
        column_positions[1]["left"] = column_positions[2]["left"] - diff
    for column_position in column_positions:
        column_position["left"] -= round(diff / 6)
    return column_positions


def _unite_separated_cells(table, column_positions):
    for row in table:
        row_length = len(row)
        if row_length > 1:
            i = 0
            while i < row_length - 1 and i < 3:
                if row[i + 1]["left"] < column_positions[i + 1]["left"]:
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


def _find_first_row(table, statement_name):
    if statement_name == "balance sheet":
        for row in table:
            if (
                "assets" in row[0]["title"].lower()
                or "capital and liabilities" in row[0]["title"].lower()
                or "equity and liabilities" in row[0]["title"].lower()
            ):
                return table.index(row)
    elif statement_name == "profit and loss":
        for row in table:
            if "income" in row[0]["title"].lower():
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
    column_names[1] = re.findall(r"\b\d{4}\b", column_names[1])[-1]
    column_names[2] = re.findall(r"\b\d{4}\b", column_names[2])[-1]
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

    unit = _find_unit(pdf_path, start, end)
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
    for i in info:
        cells.append(
            {
                "title": i["title"],
                "size": float(i["fields"]["font.size"]),
                "color": i["fields"]["font.color"],
                "bold": True if i["fields"]["font.bold"] == "true" else False,
                "left": round(float(i["fields"]["bbox.left"])),
                "right": round(float(i["fields"]["bbox.right"])),
                "top": round(float(i["fields"]["bbox.top"])),
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

        start, end = _find_table_range(table, column_positions)
        table = table[start : end + 1]

        max_right = column_positions[1]["left"] - (
            column_positions[2]["left"] - column_positions[1]["left"] * 3 / 2
        )
        _sanitize_line_break(table, _find_max_length(table), max_right)

        first_row = _find_first_row(table, statement_name)
        column_names = _find_column_names(table[0:first_row])
        table = table[first_row:]

        grading = gr.make_grading(table)
        data = _extract_data_from_table(
            statement_name, table, grading, column_names, unit
        )

        response.append(data)
    return json.dumps(response)
