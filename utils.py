import metadata as md


def extract_text_from_pdf(pdf_path, start, end):
    metadata = md.generate_range(pdf_path, start, end)
    bbox_data = md.extract(metadata, ["bbox.left", "bbox.top"])

    processed_bbox_data = []
    for bd in bbox_data:
        title, left, top = (
            bd["title"],
            round(float(bd["fields"]["bbox.left"])),
            round(float(bd["fields"]["bbox.top"])),
        )
        processed_bbox_data.append((title, left, top))
    processed_bbox_data = sorted(processed_bbox_data, key=lambda x: x[2])

    rows = []
    row = []
    last_top = None
    for title, left, top in processed_bbox_data:
        if last_top is None:
            last_top = top
        if top - last_top > 2:
            rows.append("\t".join(row))
            row = []
            last_top = top
        space = round(left / 50) - sum([len(x) for x in row])
        row.append((" " * space) + title)

    return "\n".join(rows)
