import re


def has_list_marker(title):
    pattern = r"^[\dA-Za-z]+\.\s|\([^\)]*\)\s|\s*[-*•]+(?=\s)"
    return re.match(pattern, title)


def contain_only_list_marker(title):
    # Max length of list marker is 7 ~ (viii)[space].
    return has_list_marker(title + " ") and len(title) <= 7


def remove_list_marker(title):
    pattern = r"^[\dA-Za-z]+\.\s|\([^\)]*\)\s|\s*[-*•]+(?=\s)"
    return re.sub(pattern, "", title)


def sanitize_cell_title(cell_title):
    # Pattern to match a numerical figure with commas and decimal points.
    if re.match(r"^\d{1,3}(,\d{3})*(\.\d+)?|\d+(\.\d+)?$", cell_title):
        return cell_title.replace(",", "").strip()
    if contain_only_list_marker(cell_title):
        return cell_title.strip()
    return cell_title.strip().rstrip(".")


# Remove all commas for numerical values otherwise all dots (if not list marker).
def sanitize(tables):
    for table in tables:
        for row in table:
            for cell in row:
                cell["title"] = sanitize_cell_title(cell["title"])


# Put a "-" symbol in front of the value if it is in parentheses.
def negate(title):
    if title[0] == "(" and title[-1] == ")":
        return f"-{title[1:-1]}"
    return title
