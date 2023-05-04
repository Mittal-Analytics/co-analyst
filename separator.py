def _find_separation_point(table):
    lefts = []
    for row in table:
        for cell in row[1:]:
            lefts.append(cell["left"])
    lefts.sort()
    left_count = [[lefts[0], 1]]
    for left in lefts[1:]:
        if left != left_count[-1][0]:
            left_count.append([left, 1])
        else:
            left_count[-1][1] += 1
    left_count.sort(key=lambda x: x[1], reverse=True)
    if left_count[0][1] > 25:
        return left_count[0][0] - 10
    return None


def _separate_cells(row, separation_point):
    separated_cells = [[], []]
    for cell in row:
        if cell["left"] < separation_point:
            separated_cells[0].append(cell)
        else:
            separated_cells[1].append(cell)
    return separated_cells


def separate_if_two(table):
    separation_point = _find_separation_point(table)
    if separation_point == None:
        return [table]
    separated_tables = [[], []]
    for row in table:
        separated_cells = _separate_cells(row, separation_point)
        if len(separated_cells[0]) > 0:
            separated_tables[0].append(separated_cells[0])
        if len(separated_cells[1]) > 0:
            separated_tables[1].append(separated_cells[1])
    return separated_tables
