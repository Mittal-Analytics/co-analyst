def _found_separation_point(page):
    lefts = []
    for row in page:
        for cell in row:
            lefts.append(int(cell["left"]))
    lefts.sort()

    left_count = [[lefts[0], 1]]
    for left in lefts[1:]:
        if left != left_count[-1][0]:
            left_count.append([left, 1])
        else:
            left_count[-1][1] += 1
    left_count.sort(key=lambda x: x[1], reverse=True)

    # Exclude the left values for cells of the first column.
    # TODO: 100 is an approximation. Needs to be eradicated.
    while left_count[0][0] < 100:
        left_count.pop(0)

    separation_point = None

    # TODO: 25 is an approximation. Needs to be eradicated.
    if left_count[0][1] > 25:
        separation_point = left_count[0][0]

    if separation_point:
        # -10 to detach the point from the leftmost boundary of the second page.
        separation_point -= 1

    return separation_point


def _separated_rows(row, separation_point):
    rows = [[], []]
    for cell in row:
        if cell["left"] < separation_point:
            rows[0].append(cell)
        else:
            rows[1].append(cell)
    return rows


def separated_pages_if_two(page):
    separation_point = _found_separation_point(page)
    if separation_point is None:
        return [page]
    pages = [[], []]
    for row in page:
        rows = _separated_rows(row, separation_point)
        if len(rows[0]):
            pages[0].append(rows[0])
        if len(rows[1]):
            pages[1].append(rows[1])
    return pages
