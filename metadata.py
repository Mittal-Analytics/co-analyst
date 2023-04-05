import os
import re


def _tmp_check():
    if not os.path.exists("./tmp"):
        os.mkdir("./tmp")


def generate_complete(pdf_path):
    _tmp_check()
    os.system(f"pdfxmeta {pdf_path} > ./tmp/md.txt")
    with open(f"./tmp/md.txt", "r") as f:
        metadata = f.read()
    os.remove(f"./tmp/md.txt")
    return metadata


def generate_range(pdf_path, start, end):
    _tmp_check()
    metadata = ""
    for i in range(start, end + 1):
        os.system(f"pdfxmeta -p {i} {pdf_path} > ./tmp/md.txt")
        with open(f"./tmp/md.txt", "r") as f:
            metadata += f.read()
    os.remove(f"./tmp/md.txt")
    return metadata


def extract(metadata, fields):
    matched_field_values = []

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
