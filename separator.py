def _find_separation_point(page):
    lefts = []
    for row in page:
        for cell in row:
            lefts.append(cell["left"])
    lefts.sort()
    left_count = [[lefts[0], 1]]
    for left in lefts[1:]:
        if left != left_count[-1][0]:
            left_count.append([left, 1])
        else:
            left_count[-1][1] += 1
    left_count.sort(key=lambda x: x[1], reverse=True)
    # TODO: 25 is an approximation. Needs to be eradicated.
    if left_count[0][1] > 25:
        # -1 to detach the point from the leftmost boundary of the second page.
        return left_count[0][0] - 1
    return None


def _separate_rows(row, separation_point):
    separated_rows = [[], []]
    for cell in row:
        if cell["left"] < separation_point:
            separated_rows[0].append(cell)
        else:
            separated_rows[1].append(cell)
    return separated_rows


def separate_if_two(page):
    separation_point = _find_separation_point(page)
    if separation_point == None:
        return [page]
    separated_pages = [[], []]
    for row in page:
        separated_rows = _separate_rows(row, separation_point)
        if len(separated_rows[0]):
            separated_pages[0].append(separated_rows[0])
        if len(separated_rows[1]):
            separated_pages[1].append(separated_rows[1])
    return separated_pages
