# Tools

Standalone utility scripts for book processing and analysis.

## pdf_text_extraction.py

Extracts text from PDF files using AWS Bedrock vision models and saves to JSON.

**Vision Models Used:**
- **Amazon Nova Pro** (`us.amazon.nova-pro-v1:0`) - Primary model
- **Claude 3.5 Sonnet** (`anthropic.claude-3-5-sonnet-20241022-v2:0`) - Fallback model

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

## lambda_pdf_text_extraction.py

Lambda version of PDF text extraction, triggered by EventBridge on S3 upload.

**Trigger:** EventBridge rule on S3 `PutObject` events in `bookmark-hackathon-source-files` bucket

**Process:**
1. Receives S3 upload event via EventBridge
2. Downloads PDF from S3
3. Extracts text using Bedrock vision models (Nova Pro → Claude fallback)
4. Saves JSON to same S3 bucket (replaces `.pdf` with `.json`)

**Deployment:** Not yet deployed - Lambda function ready for deployment

**Requirements:**
- Lambda layer with `pdf2image` and `poppler`
- IAM role with S3 read/write and Bedrock invoke permissions
- EventBridge rule configured for S3 uploads
