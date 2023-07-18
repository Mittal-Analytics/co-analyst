from utilities import explorer

from . import artist
from . import metadata as md
from . import separator, unifier


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
# 0 = cell1 and cell2 overlap.
# -1 = cell1 is to the left of cell2.
# 1 = cell1 is to the right of cell2.
def _find_cell_overlap(cell1, cell2):
    left1 = cell1["left"]
    right1 = cell1["right"]
    left2 = cell2["left"]
    right2 = cell2["right"]

    if right2 < left1:
        return -1
    if right1 < left2:
        return 1
    return 0


def _inject_blank_cell(row, i, left, right, top):
    row.insert(
        i,
        {
            "title": "",
            "size": None,
            "color": None,
            "bold": None,
            "left": left,
            "right": right,
            "top": top,
        },
    )


def _format_cell(table, row, i):
    overlap = _find_cell_overlap(table[0][i], row[i])
    if overlap == -1:
        _inject_blank_cell(
            table[0], i, row[i]["left"], row[i]["right"], table[0][i]["top"]
        )
    elif overlap == 1:
        _inject_blank_cell(
            row, i, table[0][i]["left"], table[0][i]["right"], row[0]["top"]
        )


def _format_row(table, row):
    for i in range(len(table[0])):
        if i < len(row):
            _format_cell(table, row, i)


def _format_table(provided_table):
    provided_table.sort(key=lambda row: len(row), reverse=True)
    table = [provided_table.pop(0)]
    while provided_table:
        row = provided_table.pop(0)
        _format_row(table, row)
        table.append(row)
    table.sort(key=lambda row: row[0]["top"])
    return table


def _table_extracted_from_page(page, table_drawing):
    table = _narrowed_page(page, table_drawing)
    # Formatting tables twice is a hack to fix the mess made by first formatting.
    table = _format_table(table)
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
        cell["title"] = cell["title"].rstrip()
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

        # TODO: We need to find a better solution than just uniting list markers.
        page = unifier.unite_separated_list_markers(page)

        # TODO: This will need to be changed while adding support for start and end.
        table = _table_extracted_from_page(page, table_drawings[0])

        column_positions = explorer.find_column_positions(table)
        table = unifier.unite_separated_cells(table, column_positions)
        table = unifier.unite_separated_rows(table, column_positions)

        extracted_tables.append(table)
    return extracted_tables
