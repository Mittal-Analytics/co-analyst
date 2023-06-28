from utilities import metadata as md
from utilities import separator, utils


def _cleaned_row(provided_row):
    row = []
    for cell in provided_row:
        if not cell["title"].strip() == "":
            row.append(cell)
    return row


# Determine if there is an overlap between two cells.
def _overlap(cell1, cell2):
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


# Find a match (format) for a provided cell against every other cell in a row.
def _found_match(provided_cell, row):
    for cell in row:
        if _overlap(provided_cell, cell):
            return row.index(cell)
    return None


# Calculate the score of a row based on how similar it is (format) to other rows.
def _calculated_score(provided_row, page):
    score = 0
    for row in page:
        matches = {}
        bad_match = False
        for cell in provided_row:
            match = _found_match(cell, row)
            if match is None:
                continue
            if match in matches and not utils.contain_only_list_marker(matches[match]):
                bad_match = True
                break
            matches[match] = cell["title"]
        if bad_match:
            continue
        score += 1
    return score


# Narrow down the page to only the rows that are part of the table.
def _narrowed_page(page):
    scores = [_calculated_score(row, page) for row in page]

    # TODO: 2 is an approximation. Needs to be eradicated.
    average_score = (sum(scores) / len(scores)) - 2

    # Remove all rows till the row that has a score less than average.
    # If the row is in the first half, remove all rows before it.
    # If the row is in the second half, remove all rows after it.
    start = 0
    end = len(scores)
    for i in range(len(scores)):
        # ith score is for the ith row.
        if scores[i] < average_score:
            if i < (len(scores) / 2):
                # +1 to not include the row with score less than average.
                start = i + 1
            else:
                # No +1 to not include the row with score less than average.
                end = i
                break

    return page[start:end]


def _table_extracted_from_page(page):
    table = _narrowed_page(page)
    return table


# Extract tables from pdf page(s).
def tables(pdf_path, start=1, end=1):
    metadata = md.page_range_metadata(pdf_path, start, end)
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
        cell["title"] = utils.sanitized(cell["title"])
        if len(row) == 0 or cell["top"] - row[0]["top"] < 1:
            row.append(cell)
        else:
            page.append(sorted(row, key=lambda x: x["left"]))
            row = [cell]
    page.append(sorted(row, key=lambda x: x["left"]))

    pages = separator.separated_pages_if_two(page)

    extracted_tables = []
    for page in pages:
        for i in range(len(page)):
            row = page[i]
            page[i] = _cleaned_row(row)

        extracted_tables.append(_table_extracted_from_page(page))
    return extracted_tables
