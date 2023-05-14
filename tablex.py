# TODO: Check if this really is the right way.
# 1aaaa
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


# 1aaa
# Finds a match (format) for a provided cell against every other cell in a row.
def _find_match(provided_cell, row):
    for cell in row:
        if _overlap(provided_cell, cell):
            return row.index(cell)
    return None


# 1aa
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


# 1a
# Remove all rows that are not part of the table.
def _clean(page):
    scores = []
    for row in page:
        score = _calculate_score(row, page)
        scores.append(score)

    average_score = sum(scores) / len(scores)

    # TODO: Remove the line below.
    # print(scores, average_score)

    # Remove all rows that did not score higher than the average score.
    for i in range(len(scores)):
        # ith score is for the ith row.
        if scores[i] < average_score:
            # TODO: Remove the line below.
            # print("Removing: ", [cell["title"] for cell in page[i]])
            page[i] = None
    while None in page:
        page.remove(None)


# 1
# "page" will have structure of page[row[cell{info}]]
def extract(page):
    _clean(page)
    # TODO: Remove the loop below.
    # for row in page:
    #     print([cell["title"] for cell in row])
    # page now is purely table.
    return page
