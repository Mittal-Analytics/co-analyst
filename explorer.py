import fitz

import metadata as md


def find_page_range(pdf_path, statement_name):
    page_ranges = []
    doc = fitz.open(pdf_path)
    for i in range(len(doc)):
        page = doc[i]
        text = page.get_text().lower()
        if statement_name in text:
            metadata = md.generate_range(pdf_path, i + 1, i + 1)
            info = md.extract(metadata, ["font.size", "font.bold"])
            cells = []
            for inf in info:
                if len(inf["title"].strip()) > 1:
                    cells.append(
                        {
                            "title": inf["title"],
                            "size": float(inf["fields"]["font.size"]),
                        }
                    )
            count = {}
            for cell in cells:
                if cell["size"] in count:
                    count[cell["size"]] += 1
                else:
                    count[cell["size"]] = 1
            for cell in cells:
                if statement_name in cell["title"].lower().strip():
                    if count[cell["size"]] <= 2:
                        page_ranges.append((i + 1, i + 1))
                    break
    return page_ranges[0]


def find_unit(pdf_path, start):
    possible_units = [
        ["trillions", "trillion"],
        ["billions", "billion"],
        ["crores", "crore"],
        ["millions", "million"],
        ["lakhs", "lakh"],
        ["thousands", "thousand"],
    ]
    possible_numerical_units = [
        ["000000000000s", "'000000000000"],
        ["000000000s", "'000000000"],
        ["0000000s", "'0000000"],
        ["000000s", "'000000"],
        ["00000s", "'00000"],
        ["000s", "'000"],
    ]
    doc = fitz.open(pdf_path)
    page = doc[start - 1]
    text = page.get_text().lower()
    for units in possible_units:
        for unit in units:
            if unit in text:
                return units[0]
    for units in possible_numerical_units:
        for unit in units:
            if unit in text:
                return possible_units[possible_numerical_units.index(units)][0]
