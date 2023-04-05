# co-analyst

I am sure you need a `co-analyst` who doesn't get tired.

## Usage

```py
import toc
import utils
import gpt

toc.generate(pdf_path, toc_path)
# generates table_of_contents.
# pdf_path is the path to the pdf you want to be processed.
# toc_path is where you want to save your table of contents.

toc.get_page_range(table_of_contents, "Heading")
# returns a tuple with start and end page for content of a
# particular heading.
# table_of_contents is actual string containg toc.
# provide heading for which you want to fetch the page range.

utils.extract_text_from_pdf(pdf_path, start, end)
# extracts text for a particular page range from a PDF in a
# very similar formatting.

gpt.extract_json_from_text(text, prompt)
# text is a little bit less structured data from which JSON
# data is expected to be extracted.
# prompt is your instructions defining the text and how to
# extract data out of it.
```
