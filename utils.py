import os
import fitz
import re
import metadata as md
import grading as gr
import json


def _find_page_range(pdf_path, statement_name):
    if statement_name.lower() == "balance sheet":
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


def _santize(cell):
    # Remove all commas for nummerical values otherwise all dots.
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


def _sanitize_line_break(table, max_length, index=0):
    if index == len(table) - 1:
        return table
    if len(table[index][0]["title"]) >= max_length - 5:
        if len(table[index]) == 1 or len(table[index + 1]) == 1:
            _merge_rows(table, table[index], table[index + 1])
    return _sanitize_line_break(table, max_length, index + 1)


def _found_first_row_match(row, column_positions):
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


def _found_last_row_match(row, column_positions):
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
        if _found_first_row_match(row, column_positions):
            table_range.append(table.index(row))
            break
    for row in table[::-1]:
        if _found_last_row_match(row, column_positions):
            table_range.append(table.index(row))
            break
    return table_range


def _find_first_row(table):
    for row in table:
        if (
            "assets" in row[0]["title"].lower()
            or "capital and liabilities" in row[0]["title"].lower()
            or "equity and liabilities" in row[0]["title"].lower()
        ):
            return table.index(row)


def _find_column_names(rows):
    column_names = []
    for row in rows:
        for cell in row:
            flag = True
            lefts = [cell["left"] for cell in column_names]
            for left in lefts:
                diff = left - cell["left"]
                if diff > 0 and diff < 50:
                    column_names[lefts.index(left)]["title"] += " " + cell["title"]
                    flag = False
                    break
            if flag:
                column_names.append(cell)
                column_names.sort(key=lambda x: x["left"])
    column_names = [cell["title"] for cell in column_names]
    if len(column_names) == 3:
        column_names.insert(0, "Particulars")
    return column_names


def _remove_list_marker(title):
    pattern = r"^[\dA-Za-z]+\.\s|\([^\)]*\)\s|\s*[-*•]+\s*"
    return re.sub(pattern, "", title).strip()


def _extract_data_from_table(table, grading, column_names):
    stack = [{"title": "Balance Sheet", "data": []}]
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
                    column_names[2]: _remove_list_marker(row[0]["title"]),
                    column_names[3]: _remove_list_marker(row[1]["title"]),
                }
            )
        elif len(row) == 3:
            stack[-1]["data"].append(
                {
                    column_names[2]: _remove_list_marker(row[1]["title"]),
                    column_names[3]: _remove_list_marker(row[2]["title"]),
                }
            )
        elif len(row) == 4:
            stack[-1]["data"].append(
                {
                    column_names[1]: _remove_list_marker(row[1]["title"]),
                    column_names[2]: _remove_list_marker(row[2]["title"]),
                    column_names[3]: _remove_list_marker(row[3]["title"]),
                }
            )

    while len(stack) > 1:
        stack[-1]["title"] = _remove_list_marker(stack[-1]["title"])
        stack[-2]["data"].append(stack[-1])
        stack.pop()

    return json.dumps(stack[0])


def extract_data_from_pdf(pdf_path, **kwargs):
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"File not found at {pdf_path}")

    try:
        start, end = kwargs["start"], kwargs["end"]
    except KeyError:
        try:
            start, end = _find_page_range(pdf_path, kwargs["statement_name"])
        except KeyError:
            raise KeyError("Either start and end or statement_name must be provided")

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

    table = []
    row = []
    for cell in cells:
        if len(row) == 0 or cell["top"] - row[-1]["top"] < 5:
            row.append(cell)
        else:
            table.append(sorted(row, key=lambda x: x["left"]))
            row = [cell]

    column_positions = _find_column_positions(table)
    table = _unite_separated_cells(table, column_positions)

    for row in table:
        for cell in row:
            cell["title"] = _santize(cell)

    start, end = _find_table_range(table, column_positions)
    table = table[start : end + 1]

    _sanitize_line_break(table, _find_max_length(table))

    first_row = _find_first_row(table)
    column_names = _find_column_names(table[0:first_row])
    table = table[first_row:]

    grading = gr.make_grading(table)
    data = _extract_data_from_table(table, grading, column_names)

    return data
