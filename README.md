# co-analyst (unstable)

I am sure you need a `co-analyst` who doesn't get tired.

## Usage

```py
import analyst

analyst.extract_data_from_pdf(pdf_path, start=123, end=123)
# pdf_path: Path to the the annual report pdf.
# start: Starting page of the statement.
# end: Ending page of the statement.
# Returns JSON data.

# OR use the format below if you do not know start and end.

# Only available for "balance sheet".
analyst.extract_data_from_pdf(pdf_path, statement_name="abc")
# pdf_path: Path to the the annual report pdf.
# statement_name: Name of the financial statement.
# Returns JSON data.
```

Currently, only extracting data from a Balance Sheet is supported
where it is on a single page.
