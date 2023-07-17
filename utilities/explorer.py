import re

import fitz

from . import metadata as md


def find_page_range(pdf_path, statement_name):
    page_ranges = []
    doc = fitz.open(pdf_path)
    for i in range(len(doc)):
        page = doc[i]
        text = page.get_text().lower()
        if statement_name in text:
            metadata = "\n".join(md.page_range_metadata(pdf_path, i + 1, i + 1))
            info = md.info_extracted_from_metadata(metadata, ["font.size", "font.bold"])
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
        "trillion",
        "billion",
        "crore",
        "million",
        "lakh",
        "thousand",
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
    for unit in possible_units:
        if unit in text:
            return unit + "s"
    for units in possible_numerical_units:
        for unit in units:
            if unit in text:
                return possible_units[possible_numerical_units.index(units)] + "s"


def find_column_positions(table):
    number_of_columns = len(table[0])
    column_positions = []
    for i in range(number_of_columns):
        column_positions.append(
            {
                "left": min([row[i]["left"] for row in table if len(row) > i]),
                "right": max([row[i]["right"] for row in table if len(row) > i]),
            }
        )
    return column_positions


def find_statement_name(pdf_path, start):
    possible_statements = [
        "profit and loss",
        "balance sheet",
    ]
    doc = fitz.open(pdf_path)
    page = doc[start - 1]
    text = page.get_text().lower()
    for statement_name in possible_statements:
        if statement_name in text:
            return statement_name
    return None


def find_max_cell_length(table):
    max_length = 0
    for row in table:
        for cell in row:
            if len(cell["title"]) > max_length:
                max_length = len(cell["title"])
    return max_length


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
