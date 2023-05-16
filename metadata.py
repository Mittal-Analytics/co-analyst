import os
import re

METADATA_PATH = "./tmp/md.txt"


# Create a temporary directory if it doesn't exist.
def _tmp_check():
    if not os.path.exists("./tmp"):
        os.mkdir("./tmp")


# Generate metadata for the whole pdf.
def generate_complete(pdf_path):
    _tmp_check()
    os.system(f"pdfxmeta {pdf_path} > {METADATA_PATH}")
    with open(f"{METADATA_PATH}", "r") as f:
        metadata = f.read()
    os.remove(f"{METADATA_PATH}")
    return metadata


# Generate metadata for a range of pages.
# index for "start" and "end" starts from 1 (not 0).
def generate_range(pdf_path, start, end):
    _tmp_check()
    metadata = ""
    for i in range(start, end + 1):
        os.system(f"pdfxmeta -p {i} {pdf_path} > {METADATA_PATH}")
        with open(f"{METADATA_PATH}", "r") as f:
            metadata += f.read()
    os.remove(f"{METADATA_PATH}")
    return metadata


# Extract particular properties along with title from metadata.
def extract(metadata, fields):
    matched_field_values = []

    # "field" will have a structure of "a.b".
    for field in fields:
        a, b = field.split(".")
        pattern = r"^\s*" + a + r"\." + b + r" = (.+)\n"
        matches = re.findall(pattern, metadata, re.MULTILINE)
        matched_field_values.append(matches)

    title_pattern = r"^\s*(.+):\s*\n(?:\s+.+\n)"
    title_matches = re.findall(title_pattern, metadata, re.MULTILINE)

    response = []

    for i in range(len(title_matches)):
        res = {"title": title_matches[i], "fields": {}}
        for field, field_matches in zip(fields, matched_field_values):
            res["fields"][field] = field_matches[i]
        response.append(res)
    return response
