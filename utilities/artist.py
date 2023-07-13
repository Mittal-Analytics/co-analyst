import fitz


def _min_x(x):
    return min(min(f[1][0], f[2][0]) for f in x)


def _min_y(x):
    return min(min(f[1][1], f[2][1]) for f in x)


def _is_too_far(figure_group, provided_figure):
    for figure in figure_group:
        if (
            abs(figure[1][1] - provided_figure[1][1]) < 1
            or abs(figure[2][1] - provided_figure[1][1]) < 1
            or abs(figure[1][1] - provided_figure[2][1]) < 1
            or abs(figure[2][1] - provided_figure[2][1]) < 1
        ):
            return False
    return True


def _is_top_left_vertex_present(figure_group):
    min_x = min(min(figure[1][0], figure[2][0]) for figure in figure_group)
    min_y = min(min(figure[1][1], figure[2][1]) for figure in figure_group)
    count = 0
    for figure in figure_group:
        if figure[0] == "re":
            if (
                abs(min(figure[1][0], figure[2][0]) - min_x) < 1
                and abs(min(figure[1][1], figure[2][1]) - min_y) < 1
            ):
                count += 2
        elif (
            abs(min(figure[1][0], figure[2][0]) - min_x) < 1
            and abs(min(figure[1][1], figure[2][1]) - min_y) < 1
        ):
            count += 1
        if count > 1:
            return True
    return False


def _find_top_left_vertex(figure_group):
    indexes = []
    for i in range(len(figure_group)):
        if _is_top_left_vertex_present(figure_group[i:]):
            indexes.append(i)
    tables = []
    if len(indexes):
        while len(indexes) > 1:
            tables.append(figure_group[indexes[0] : indexes[1]])
            indexes.pop(0)
        tables.append(figure_group[indexes[0] :])
    else:
        tables.append(figure_group)
    return tables


# TODO: Make sure this is efficient.
def _is_overlapping(table1, table2):
    t1_min_x = _min_x(table1)
    t1_min_y = _min_y(table1)
    t1_max_x = max(max(f[1][0], f[2][0]) for f in table1)
    t1_max_y = max(max(f[1][1], f[2][1]) for f in table1)
    t2_min_x = _min_x(table2)
    t2_min_y = _min_y(table2)
    t2_max_x = max(max(f[1][0], f[2][0]) for f in table2)
    t2_max_y = max(max(f[1][1], f[2][1]) for f in table2)
    if (
        t1_min_x <= t2_min_x <= t1_max_x
        or t1_min_x <= t2_max_x <= t1_max_x
        or t2_min_x <= t1_min_x <= t2_max_x
        or t2_min_x <= t1_max_x <= t2_max_x
    ) and (
        t1_min_y <= t2_min_y <= t1_max_y
        or t1_min_y <= t2_max_y <= t1_max_y
        or t2_min_y <= t1_min_y <= t2_max_y
        or t2_min_y <= t1_max_y <= t2_max_y
    ):
        return True
    return False


def _invalid_tables_removed(tables):
    invalid = False
    new_tables = []
    for table in tables:
        if _is_top_left_vertex_present(table):
            if new_tables and _is_overlapping(new_tables[-1], table):
                new_tables[-1].extend(table)
                invalid = True
            else:
                new_tables.append(table)
        elif new_tables:
            new_tables[-1].extend(table)
            invalid = True
    if invalid:
        return _invalid_tables_removed(new_tables)
    return new_tables


def _find_tables(figures):
    figure_groups = [[figures[0]]]
    for figure in figures[1:]:
        is_figure_appended = False
        # TODO: There's a possibility of figures messing up the sort here.
        for figure_group in figure_groups[::-1]:
            if not _is_too_far(figure_group, figure):
                figure_group.append(figure)
                is_figure_appended = True
                break
        if not is_figure_appended:
            figure_groups.append([figure])
    tables = []
    for figure_group in figure_groups:
        tables.extend(_find_top_left_vertex(figure_group))
    tables.sort(key=lambda x: (_min_y(x), _min_x(x)))
    tables = _invalid_tables_removed(tables)
    return tables


def get_table_drawings(pdf_path, start, end):
    drawings = []
    doc = fitz.open(pdf_path)
    pages = []
    for page in doc:
        if page.number + 1 >= start and page.number + 1 <= end:
            pages.append(page)
    for page in pages:
        paths = page.get_cdrawings()
        figures = []
        for path in paths:
            for item in path["items"]:
                if item[0] == "l":
                    # Only straight lines.
                    if item[1][0] == item[2][0] or item[1][1] == item[2][1]:
                        figures.append(item)
                elif item[0] == "re":
                    figures.append(
                        ["re", (item[1][0], item[1][1]), (item[1][2], item[1][3])]
                    )
        figures.sort(key=lambda x: (x[1][1], x[1][0]))
        tables = _find_tables(figures)
        drawings.append(tables)
    return drawings


def get_coordinates(table_drawing):
    min_x = _min_x(table_drawing)
    min_y = _min_y(table_drawing)
    max_x = max(max(f[1][0], f[2][0]) for f in table_drawing)
    max_y = max(max(f[1][1], f[2][1]) for f in table_drawing)
    return min_x, min_y, max_x, max_y
