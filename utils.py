import re


def has_list_marker(title):
    pattern = r"^[\dA-Za-z]+\.\s|\([^\)]*\)\s|\s*[-*•]+(?=\s)"
    return re.match(pattern, title)


def contain_only_list_marker(title):
    # Max length of list marker is 7 ~ (viii)[space].
    return len(title) <= 7 and has_list_marker(title + " ")


def remove_list_marker(title):
    pattern = r"^[\dA-Za-z]+\.\s|\([^\)]*\)\s|\s*[-*•]+(?=\s)"
    return re.sub(pattern, "", title)


# Remove all commas for numerical values otherwise all dots (if not list marker).
def sanitized(cell_title):
    if re.match(r"^\d{1,3}(,\d{3})*(\.\d+)?|\d+(\.\d+)?$", cell_title):
        return cell_title.replace(",", "").strip()
    # Max length of list marker is 7 ~ (viii)[space].
    if contain_only_list_marker(cell_title):
        return cell_title.strip()
    return cell_title.rstrip(".").strip()


# Put a "-" symbol in front of the value if it is in parentheses.
def negate(title):
    if title[0] == "(" and title[-1] == ")":
        return f"-{title[1:-1]}"
    return title
