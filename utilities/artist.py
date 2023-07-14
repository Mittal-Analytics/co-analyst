import fitz


def _min_x(figure_group):
    return min(min(f["x0"], f["x1"]) for f in figure_group)


def _min_y(figure_group):
    return min(min(f["y0"], f["y1"]) for f in figure_group)


def _max_x(figure_group):
    return max(max(f["x0"], f["x1"]) for f in figure_group)


def _max_y(figure_group):
    return max(max(f["y0"], f["y1"]) for f in figure_group)


def _is_too_far(figure_group, provided_figure):
    for figure in figure_group:
        if (
            abs(figure["y0"] - provided_figure["y0"]) < 1
            or abs(figure["y1"] - provided_figure["y0"]) < 1
            or abs(figure["y0"] - provided_figure["y1"]) < 1
            or abs(figure["y1"] - provided_figure["y1"]) < 1
        ):
            return False
    return True


def _is_top_left_vertex_present(figure_group):
    min_x = _min_x(figure_group)
    min_y = _min_y(figure_group)
    count = 0
    for figure in figure_group:
        if (
            abs(min(figure["x0"], figure["x1"]) - min_x) < 1
            and abs(min(figure["y0"], figure["y1"]) - min_y) < 1
        ):
            if figure["type"] == "re":
                count += 2
            else:
                count += 1
        if count > 1:
            return True
    return False


def _top_left_vertex_separated(figure_group):
    indexes = []
    figure_group_len = len(figure_group)
    for i in range(figure_group_len):
        if _is_top_left_vertex_present(figure_group[i:]):
            indexes.append(i)
    separated_figure_groups = []
    if indexes:
        while len(indexes) > 1:
            separated_figure_groups.append(figure_group[indexes[0] : indexes[1]])
            indexes = indexes[1:]
        separated_figure_groups.append(figure_group[indexes[0] :])
    else:
        separated_figure_groups.append(figure_group)
    return separated_figure_groups


# TODO: Make sure this is efficient.
def _is_overlapping(table1, table2):
    t1_min_x = _min_x(table1)
    t1_min_y = _min_y(table1)
    t1_max_x = _max_x(table1)
    t1_max_y = _max_y(table1)
    t2_min_x = _min_x(table2)
    t2_min_y = _min_y(table2)
    t2_max_x = _max_x(table2)
    t2_max_y = _max_y(table2)
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


def _removed_and_merged(table_drawings):
    invalid = False
    new_table_drawings = []
    for td in table_drawings:
        if _is_top_left_vertex_present(td):
            if new_table_drawings and _is_overlapping(new_table_drawings[-1], td):
                new_table_drawings[-1].extend(td)
                invalid = True
            else:
                new_table_drawings.append(td)
        elif new_table_drawings:
            new_table_drawings[-1].extend(td)
            invalid = True
    if invalid:
        return _removed_and_merged(new_table_drawings)
    return new_table_drawings


def _find_table_drawings(figures):
    if not figures:
        return []
    figure_groups = [[figures[0]]]
    for figure in figures[1:]:
        is_figure_appended = False
        for figure_group in figure_groups[::-1]:
            if not _is_too_far(figure_group, figure):
                figure_group.append(figure)
                is_figure_appended = True
                break
        if not is_figure_appended:
            figure_groups.append([figure])
    table_drawings = []
    for figure_group in figure_groups:
        table_drawings.extend(_top_left_vertex_separated(figure_group))
    table_drawings = _removed_and_merged(table_drawings)
    return table_drawings


def get_table_drawings(pdf_path, start, end):
    table_drawings = []
    doc = fitz.open(pdf_path)
    pages = []
    for i in range(start - 1, end):
        pages.append(doc[i])
    for page in pages:
        paths = page.get_cdrawings()
        figures = []
        for path in paths:
            for item in path["items"]:
                if item[0] == "l":
                    # Only straight lines.
                    if item[1][0] == item[2][0] or item[1][1] == item[2][1]:
                        figures.append(
                            {
                                "type": "l",
                                "x0": item[1][0],
                                "y0": item[1][1],
                                "x1": item[2][0],
                                "y1": item[2][1],
                            }
                        )
                elif item[0] == "re":
                    figures.append(
                        {
                            "type": "re",
                            "x0": item[1][0],
                            "y0": item[1][1],
                            "x1": item[1][2],
                            "y1": item[1][3],
                        }
                    )
                # If the figure is extracted in reverse order, swap the coordinates.
                if figures and (
                    figures[-1]["x0"] > figures[-1]["x1"]
                    or figures[-1]["y0"] > figures[-1]["y1"]
                ):
                    figures[-1]["x0"], figures[-1]["x1"] = (
                        figures[-1]["x1"],
                        figures[-1]["x0"],
                    )
                    figures[-1]["y0"], figures[-1]["y1"] = (
                        figures[-1]["y1"],
                        figures[-1]["y0"],
                    )
        figures.sort(key=lambda f: (f["y0"], f["x0"]))
        table_drawings.append(_find_table_drawings(figures))
    return table_drawings


def get_coordinates(table_drawing):
    min_x = _min_x(table_drawing)
    min_y = _min_y(table_drawing)
    max_x = _max_x(table_drawing)
    max_y = _max_y(table_drawing)
    return min_x, min_y, max_x, max_y
