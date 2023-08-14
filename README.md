# co-analyst (broken)

I am sure you need a `co-analyst` who doesn't get tired.

## Usage

```py
import analyst

analyst.extract_data_from_pdf(pdf_path, start=123, end=123)
# pdf_path: Path to the the annual report pdf.
# start: Starting page of the financial statement.
# end: Ending page of the financial statement.
# Returns JSON data.

# OR use the format below if you do not know start and end.

analyst.extract_data_from_pdf(pdf_path, statement_name="abc")
# pdf_path: Path to the the annual report pdf.
# statement_name: Name of the financial statement.
# Returns JSON data.
```

## Development Environment Setup

```shell
# Clone the repository and setup virtual environment.
git clone git@github.com:Mittal-Analytics/co-analyst.git
cd co-analyst
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies.
pip install -r requirements/requirements-dev.txt

# Run tests to make sure everything is working fine.
python -m unittest
```

**Note:** This setup assumes you have `git`, `python` and `pip` installed.

## Behind the Scenes

If you explore the utilities folder, you'll see multiple modules that are essential
for the working of this package. Let's go through each of them one by one.

**But first,**

Let's assume you have a financial statement to read. Maybe, it's a balance sheet.
What format is the balance sheet in? Voila, It's a table and so is every other
financial statement.

Now, If I ask you **what makes it easier for a person to read from a table**? You might say, _A table is in a certain format that contains rows and columns. These rows and columns are easy to identify because they are separated by lines. All the data in the table is put under their respective rows and columns. The headings are often put in the first row and the first column and is made bold. All these things make it easy for a person to read a table._

This is exactly what `co-analyst` look for while converting a particular financial
statement into a JSON format.

**Before reading further,** you should know the structure of a cell in the table.

```py
{
    "title": str,
    "size": float,
    "color": str,
    "bold": bool,
    "left": float, # x0
    "right": float, # x1
    "top": float, # y0
}
```

**...and** `pdf_path` is the path to the pdf file.\
**...and** `table` is a list of list (rows) of cells.

**Now,** let's start with exploring the modules.

### tablex.py

The `extract_tables` function of this module is where all the magic begins. It takes a pdf file and a page number as input and returns a list of tables that are fully formatted and ready to be converted into JSON.

```py
extract_tables(pdf_path, page_num)
# page_num: Page number of the page you want to extract the tables from.
# If omitted, it will extract tables from the first page of the pdf, if any exists.
# Returns a list of tables.
```

### metadata.py

```py
complete_metadata(pdf_path)
# Returns metadata of the whole pdf.

page_range_metadata(pdf_path, start, end)
# Returns metadata of the pages in the given range.

info_extracted_from_metadata(metadata, fields)
# metadata: Metadata of the pdf or range of pages.
# fields: List of fields you want to extract from the metadata.
# Like, font.size, font.color, etc.
# Returns a list of dictionaries containing the extracted information.
```

_This module depends on `pdf-tocgen` which will be replaced by a function of `pymupdf` soon removing the functions `complete_metadata` and `page_range_metadata`._

### unifier.py

```py
unite_separated_list_markers(table)
# Returns a list of list (rows) with the list markers merged with the next cell int the row.

unite_separated_rows(table, column_positions)
# column_positions: The list of x0 (start), x1 (end) values of columns.
# Returns a list of list (rows) with the rows merged with the next row
# if they match certain criterion.
```

### artist.py

This is a game changing module leveraging the `get_cdrawings` function of `pymupdf` to extract the structure (lines and rectangles) of a table so that it can be used to extract the data from the table efficiently and effectively.

```py
get_table_drawings(pdf_path, page_num)
# page_num: Page number of the page you want to extract the tables from.
# Returns a list of structures (drawings) of all the tables a certain page contains.

get_min_max_coordinates(table_drawing)
# table_drawing: This is what "get_table_drawings" returns.
# Returns the minimum and maximum x0 (start), x1 (end),
# y0 (top), y1 (bottom) values of the table.
```

### explorer.py

```py
find_page_range(pdf_path, statement_name)
# statement_name: Name of the financial statement.
# Returns the starting and ending page number of the financial statement.

find_unit(pdf_path, page_num)
# page_num: Page number of the page you want to extract the unit from.
# Usually the first page of the financial statement.
# Returns the unit of the financial statement.

find_column_positions(table)
# Returns a list of x0 (start), x1 (end) values of columns.

find_statement_name(pdf_path, page_num)
# page_num: Page number of the page you want to extract the statement name from.
# Usually the first page of the financial statement.

find_max_cell_length(table)
# Returns the maximum length of a cell["title"] in the table.

find_first_row(table)
# Returns the index of the row that contain the cells matching certain keywords like
# "assets", "capital and liabilities", etc. to identify the row next to the header
# of the table since header splits into multiple rows in many cases.

find_column_names(rows)
# rows: A list that contains all the rows that are above the first row.
# Returns a list of column names.
```

### grader.py

This module is the primary thing we use outside of the `tablex.py` module that helps us classify different cells as `heading`, `sub-heading` or `value` based on further processing.

```py
get_grading(table)
# table: A list of list (rows).
# Returns a list of cell["title"] with their grades.
```

_Same grade signifies same level._

### tools.py

This module contains some utility functions that are used by other modules which have a self explanatory name. You can go through `tools.py` to learn more.

```py
has_list_marker(title)
contain_only_list_marker(title)
remove_list_marker(title)
sanitize_cell_title(cell_title)
negate(title)
```

## The Future

The vision is to make `tablex.py` so good that it can extract formatted tables from any page no matter if it is a financial statement or not. `co-analyst` on the other hand will leverage `tablex.py` to convert specifically financial statements into a JSON format by adding customizations on top, maybe by leveraging AI/ML.
