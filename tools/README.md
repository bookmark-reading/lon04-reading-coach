# Tools

Standalone utility scripts for book processing and analysis.

## pdf_text_extraction.py

Extracts text from PDF files using AWS Bedrock vision models and saves to JSON.

**Purpose:** One-time processing of PDF books to create structured JSON files with page text, types, and summaries. This is so the contents of the books by page can be retrieved by the app to analyse against the child's reading.

**Usage:**
```bash
python pdf_text_extraction.py \
  --bucket bookmark-hackathon-source-files \
  --pdf "L.2 - Bathtub Safari.pdf" \
  --output-dir ../resources/books/
```

**Output:** Creates `{pdf_name}_pages.json` with structured page data:
```json
{
  "1": {
    "type": "cover|story|blank|comprehension|ignore",
    "text": "extracted text",
    "summary": "child-friendly summary under 25 words"
  }
}
```

**Requirements:**
- AWS credentials with Bedrock access
- `pdf2image` library
- `poppler-utils` system package

**Note:** This is a preprocessing tool, not part of the main application runtime.
