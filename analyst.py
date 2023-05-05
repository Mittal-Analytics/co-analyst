import json
import os

import explorer
import grader
import metadata as md
import separator
import unifier
import utils


def _extract_data_from_table(statement_name, table, grading, column_names, unit):
    stack = [{"title": statement_name, "unit": unit, "data": []}]
    for row in table:
        try:
            while (
                len(stack) > 1
                and grading[row[0]["title"]] >= grading[stack[-1]["title"]]
            ):
                stack[-1]["title"] = utils.remove_list_marker(stack[-1]["title"])
                stack[-2]["data"].append(stack[-1])
                stack.pop()
        except KeyError:
            if len(row) == 2:
                stack[-1]["title"] = utils.remove_list_marker(stack[-1]["title"])
                stack[-2]["data"].append(stack[-1])
                stack.pop()
        stack.append({"title": row[0]["title"], "data": []})
        if len(row) == 2:
            stack[-1]["title"] = stack[-2]["title"]
            stack[-1]["data"].append(
                {
                    column_names[1]: utils.negate(
                        utils.remove_list_marker(row[0]["title"])
                    ),
                    column_names[2]: utils.negate(
                        utils.remove_list_marker(row[1]["title"])
                    ),
                }
            )
        elif len(row) == 3:
            stack[-1]["data"].append(
                {
                    column_names[1]: utils.negate(
                        utils.remove_list_marker(row[1]["title"])
                    ),
                    column_names[2]: utils.negate(
                        utils.remove_list_marker(row[2]["title"])
                    ),
                }
            )
        elif len(row) == 4:
            stack[-1]["data"].append(
                {
                    column_names[0]: utils.remove_list_marker(row[1]["title"]),
                    column_names[1]: utils.negate(
                        utils.remove_list_marker(row[2]["title"])
                    ),
                    column_names[2]: utils.negate(
                        utils.remove_list_marker(row[3]["title"])
                    ),
                }
            )

    while len(stack) > 1:
        stack[-1]["title"] = utils.remove_list_marker(stack[-1]["title"])
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
        column_positions = explorer.find_column_positions(table)
        table = unifier.unite_separated_cells(table, column_positions)

        for row in table:
            for cell in row:
                cell["title"] = utils.sanitize(cell)

        statement_name = explorer.find_statement_name(table)

        max_cell_right = column_positions[1]["left"] - (
            column_positions[2]["left"] - column_positions[1]["left"] * 3 / 2
        )
        unifier.unite_separated_rows(
            table, explorer.find_max_cell_length(table), max_cell_right
        )

        start, end = explorer.find_table_range(table, column_positions)
        table = table[start : end + 1]

        first_row = explorer.find_first_row(table)
        column_names = explorer.find_column_names(table[0:first_row])
        table = table[first_row:]

        grading = grader.make_grading(table)
        data = _extract_data_from_table(
            statement_name, table, grading, column_names, unit
        )

        if data["title"] == None:
            response[-1]["data"].append(data["data"][0])
        else:
            response.append(data)
    return json.dumps(response)
