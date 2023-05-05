import re


def sanitize(cell):
    # Remove all commas for numerical values otherwise all dots.
    if re.match(r"^\d{1,3}(,\d{3})*(\.\d+)?|\d+(\.\d+)?$", cell["title"]):
        return cell["title"].replace(",", "").strip()
    return cell["title"].rstrip(".").strip()


def remove_list_marker(title):
    pattern = r"^[\dA-Za-z]+\.\s|\([^\)]*\)\s|\s*[-*•]+(?=\s)"
    return re.sub(pattern, "", title).strip()


def negate(title):
    if title[0] == "(" and title[-1] == ")":
        return f"-{title[1:-1]}"
    return title
