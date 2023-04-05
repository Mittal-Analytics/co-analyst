import os
import re
import metadata as md


def generate(pdf_path, toc_path):
    metadata = md.generate_complete(pdf_path)
    font_data = md.extract(metadata, ["font.size"])

    font_sizes = []
    for fd in font_data:
        font_sizes.append(fd["fields"]["font.size"])

    font_size_frequency = []
    for font_size in font_sizes:
        count = font_sizes.count(font_size)
        font_size_frequency.append((float(font_size), count))
        while count:
            font_sizes.remove(font_size)
            count -= 1
    font_size_frequency = sorted(font_size_frequency, reverse=True)

    # TODO: Solve the accuracy problem.
    heading = max(font_size_frequency[:16], key=lambda x: x[1])

    # heading[0], because tuple: (font_size, count).
    recipe = f"""[[heading]]
    level = 1
    greedy = true
    font.size = {heading[0]}
    """

    recipe_path = "./tmp/recipe.toml"
    with open(recipe_path, "w") as f:
        f.write(recipe)
    os.system(f"pdftocgen {pdf_path} < {recipe_path} > {toc_path}")
    os.remove(recipe_path)


def get_page_range(toc, heading):
    if len(toc) == 0:
        raise ValueError("Table of contents is empty.")

    contents = re.findall(r'"(.+?)" (\d+)', toc)

    # TODO: Improve Algo.
    start = None
    end = None
    for content in contents:
        content_heading = content[0].strip()
        content_page_number = int(content[1])
        if heading.lower() in content_heading.lower():
            start = content_page_number
            continue
        if start:
            end = content_page_number
            break

    return (start, max(start, end - 1))
