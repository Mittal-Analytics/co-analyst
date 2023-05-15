import re


# Remove all commas for numerical values otherwise all dots.
def sanitized(cell_title):
    if re.match(r"^\d{1,3}(,\d{3})*(\.\d+)?|\d+(\.\d+)?$", cell_title):
        return cell_title.replace(",", "").strip()
    return cell_title.rstrip(".").strip()


def remove_list_marker(title):
    pattern = r"^[\dA-Za-z]+\.\s|\([^\)]*\)\s|\s*[-*•]+(?=\s)"
    return re.sub(pattern, "", title)


# Put a "-" symbol in front of the value if it is in parentheses.
def negate(title):
    if title[0] == "(" and title[-1] == ")":
        return f"-{title[1:-1]}"
    return title
