# co-analyst (beta)

I am sure you need a `co-analyst` who doesn't get tired.

## Usage

```py
import utils

utils.extract_data_from_pdf(pdf_path, start, end)
# pdf_path: Path to the the annual report pdf.
# start: Starting page of the statement.
# end: Ending page of the statement.
# Returns JSON data.
```

Currently, only extracting data from a Balance Sheet is supported
where it is on a single page and is the only thing in that page.
