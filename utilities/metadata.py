import os
import re

TMP_FOLDER = "./tmp"
METADATA_FILE = f"{TMP_FOLDER}/md.txt"


# Create a temporary directory if it doesn't exist.
def _tmp_check():
    if not os.path.exists(TMP_FOLDER):
        os.mkdir(TMP_FOLDER)


# Generate metadata for the whole pdf.
def complete_metadata(pdf_path):
    _tmp_check()
    os.system(f"pdfxmeta {pdf_path} > {METADATA_FILE}")
    with open(METADATA_FILE, "r") as f:
        metadata = f.read()
    os.remove(METADATA_FILE)
    return metadata


# Generate metadata for a range of pages.
# index for "start" and "end" starts from 1 (not 0).
def page_range_metadata(pdf_path, start, end):
    _tmp_check()
    metadata = []
    for i in range(start, end + 1):
        os.system(f"pdfxmeta -p {i} {pdf_path} > {METADATA_FILE}")
        with open(METADATA_FILE, "r") as f:
            metadata.append(f.read())
    os.remove(METADATA_FILE)
    return metadata


# Extract particular properties along with title from metadata.
def info_extracted_from_metadata(metadata, fields):
    matched_field_values = []

    # "field" will always have a structure of "a.b".
    for field in fields:
        a, b = field.split(".")
        pattern = r"^\s*" + a + r"\." + b + r" = (.+)\n"
        matches = re.findall(pattern, metadata, re.MULTILINE)
        matched_field_values.append(matches)

    title_pattern = r"^\s*(.+):\s*\n(?:\s+.+\n)"
    title_matches = re.findall(title_pattern, metadata, re.MULTILINE)

    metadata = []
    title_matches_length = len(title_matches)
    for i in range(title_matches_length):
        res = {"title": title_matches[i], "fields": {}}
        for field, field_matches in zip(fields, matched_field_values):
            res["fields"][field] = field_matches[i]
        metadata.append(res)
    return metadata
