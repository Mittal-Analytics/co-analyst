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


# Finds a match (format) for a provided cell against every other cell in a row.
def _find_match(provided_cell, row):
    for cell in row:
        if _overlap(provided_cell, cell):
            return row.index(cell)
    return None


# Calculates the score of a row based on how similar it is (format) to other rows.
def _calculate_score(provided_row, page):
    score = 0
    for row in page:
        matches = []
        for cell in provided_row:
            match = _find_match(cell, row)
            if match == None:
                continue
            if match in matches:
                matches = []
                break
            matches.append(match)
        if len(matches) == 0:
            continue
        score += 1
    return score


# Remove all rows that are not part of the table.
def _clean(page):
    scores = []
    for row in page:
        score = _calculate_score(row, page)
        scores.append(score)

    average_score = sum(scores) / len(scores)

    # Remove all rows till the row that has a score less than average.
    # If the row is in the first half, remove all rows before it.
    # If the row is in the second half, remove all rows after it.
    for i in range(len(scores)):
        # ith score is for the ith row.
        if scores[i] < average_score:
            if i < len(scores) / 2:
                for j in range(i + 1):
                    page[j] = None
            else:
                for j in range(i, len(scores)):
                    page[j] = None
                break
    while None in page:
        page.remove(None)


# "page" will have structure of page[row[cell{info}]]
def extract(page):
    _clean(page)
    # page now is purely table.
    return page
