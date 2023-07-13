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
    x0, y0, x1, y1 = artist.get_coordinates(table_drawing)
    table = []
    for row in page:
        for cell in row:
            if cell["top"] >= y0 and cell["top"] <= y1:
                table.append(row)
                break
    return table


def _table_extracted_from_page(page, table_drawing):
    table = _narrowed_page(page, table_drawing)
    for row in table:
        print([cell["title"] for cell in row])
    return table


# Extract tables from pdf page(s).
def extract_tables(pdf_path, start=1, end=1):
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
        extracted_tables.append(
            _table_extracted_from_page(page, table_drawings[pages.index(page)])
        )
    return extracted_tables
