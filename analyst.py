import json
import os

from utilities import explorer, grader, tablex, tools, unifier


def _extract_data_from_table(statement_name, table, grading, column_names, unit):
    stack = [{"title": statement_name, "unit": unit, "data": []}]
    for row in table:
        try:
            while (
                len(stack) > 1
                and grading[row[0]["title"]] >= grading[stack[-1]["title"]]
            ):
                stack[-1]["title"] = tools.remove_list_marker(stack[-1]["title"])
                stack[-2]["data"].append(stack[-1])
                stack.pop()
        except KeyError:
            if len(row) == 2:
                stack[-1]["title"] = tools.remove_list_marker(stack[-1]["title"])
                stack[-2]["data"].append(stack[-1])
                stack.pop()
        stack.append({"title": row[0]["title"], "data": []})
        if len(row) == 2:
            stack[-1]["title"] = stack[-2]["title"]
            stack[-1]["data"].append(
                {
                    column_names[1]: tools.negate(
                        tools.remove_list_marker(row[0]["title"])
                    ),
                    column_names[2]: tools.negate(
                        tools.remove_list_marker(row[1]["title"])
                    ),
                }
            )
        elif len(row) == 3:
            stack[-1]["data"].append(
                {
                    column_names[1]: tools.negate(
                        tools.remove_list_marker(row[1]["title"])
                    ),
                    column_names[2]: tools.negate(
                        tools.remove_list_marker(row[2]["title"])
                    ),
                }
            )
        elif len(row) == 4:
            stack[-1]["data"].append(
                {
                    column_names[0]: tools.remove_list_marker(row[1]["title"]),
                    column_names[1]: tools.negate(
                        tools.remove_list_marker(row[2]["title"])
                    ),
                    column_names[2]: tools.negate(
                        tools.remove_list_marker(row[3]["title"])
                    ),
                }
            )

    while len(stack) > 1:
        stack[-1]["title"] = tools.remove_list_marker(stack[-1]["title"])
        stack[-2]["data"].append(stack[-1])
        stack.pop()

    return stack[0]


def extract_data_from_pdf(pdf_path, **kwargs):
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"File not found at {pdf_path}.")

    try:
        start, end = kwargs["start"], kwargs["end"]
        statement_name = explorer.find_statement_name(pdf_path, start)
    except KeyError:
        try:
            statement_name = kwargs["statement_name"].lower()
            start, end = explorer.find_page_range(pdf_path, statement_name)
        except KeyError:
            raise KeyError("Either start and end or statement_name must be provided.")

    unit = explorer.find_unit(pdf_path, start)
    tables = tablex.extract_tables(pdf_path, start, end)

    response = []
    for table in tables:
        column_positions = explorer.find_column_positions(table)
        table = unifier.unite_separated_cells(table, column_positions)

        max_cell_right = column_positions[1]["left"] - (
            column_positions[2]["left"] - column_positions[1]["left"] * 3 / 2
        )
        # TODO: Modify this function to unite rows no matter what column position.
        unifier.unite_separated_rows(
            table, explorer.find_max_cell_length(table), max_cell_right
        )

        first_row = explorer.find_first_row(table)
        column_names = explorer.find_column_names(table[0:first_row])
        table = table[first_row:]

        grading = grader.make_grading(table)
        data = _extract_data_from_table(
            statement_name, table, grading, column_names, unit
        )

        # data["title"] will be None when table on the current page
        # is continuation of the table of the previous page.
        if data["title"] is None:
            response[-1]["data"].append(data["data"][0])
        else:
            response.append(data)
    return json.dumps(response)
