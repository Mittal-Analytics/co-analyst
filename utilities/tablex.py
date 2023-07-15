from utilities import artist
from utilities import metadata as md
from utilities import separator, tools


def _empty_cells_removed(provided_row):
    row = []
    for cell in provided_row:
        if not cell["title"].strip() == "":
            row.append(cell)
    return row


# Narrow down the page to only the rows that are part of the table.
def _narrowed_page(page, table_drawing):
    x0, y0, x1, y1 = artist.get_min_max_coordinates(table_drawing)
    table = []
    for row in page:
        for cell in row:
            if cell["top"] >= y0 and cell["top"] <= y1:
                table.append(row)
                break
    return table


# Determine if there is an overlap between two cells.
def _is_overlapping(cell1, cell2):
    left1 = cell1["left"]
    right1 = cell1["right"]
    left2 = cell2["left"]
    right2 = cell2["right"]

    if left1 <= left2 <= right1:
        return True
    if left1 <= right2 <= right1:
        return True
    if left2 <= left1 <= right2:
        return True
    if left2 <= right1 <= right2:
        return True
    return False


def _format_table(provided_table):
    provided_table.sort(key=lambda row: len(row), reverse=True)
    table = [provided_table.pop(0)]
    while provided_table:
        row = provided_table.pop(0)
        for i in range(len(table[0])):
            if i < len(row) and _is_overlapping(row[i], table[0][i]):
                continue
            row.insert(
                i,
                {
                    "title": "",
                    "size": None,
                    "color": None,
                    "bold": None,
                    "left": table[0][i]["left"],
                    "right": table[0][i]["right"],
                    "top": row[0]["top"],
                },
            )
        table.append(row)
    table.sort(key=lambda row: row[0]["top"])
    return table


def _table_extracted_from_page(page, table_drawing):
    table = _narrowed_page(page, table_drawing)
    table = _format_table(table)
    return table


# Extract tables from pdf page(s).
def extract_tables(pdf_path, start=1, end=1):
    # TODO: This will need to be changed while adding support for start and end.
    table_drawings = artist.get_table_drawings(pdf_path, start, end)[0]
    metadata = "\n".join(md.page_range_metadata(pdf_path, start, end))
    info = md.info_extracted_from_metadata(
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

    page = []
    row = []
    for cell in cells:
        cell["title"] = tools.sanitize(cell["title"])
        if len(row) == 0 or cell["top"] - row[0]["top"] < 1:
            row.append(cell)
        else:
            page.append(sorted(row, key=lambda x: x["left"]))
            row = [cell]
    page.append(sorted(row, key=lambda x: x["left"]))

    pages = separator.separate_pages_if_two(page)

    extracted_tables = []
    for page in pages:
        for i in range(len(page)):
            row = page[i]
            page[i] = _empty_cells_removed(row)
        # TODO: This will need to be changed while adding support for start and end.
        extracted_tables.append(_table_extracted_from_page(page, table_drawings[0]))
    return extracted_tables
