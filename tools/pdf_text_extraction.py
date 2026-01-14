#!/usr/bin/env python3
"""
PDF Text Extraction
Extract text from PDF using vision models and save to JSON
"""

import boto3
import json
import os
import argparse
import base64
from typing import Dict
from pdf2image import convert_from_bytes
from io import BytesIO

class PDFTextExtractor:
    def __init__(self, aws_access_key=None, aws_secret_key=None, aws_session_token=None, region='us-west-2'):
        if aws_access_key and aws_secret_key:
            os.environ['AWS_ACCESS_KEY_ID'] = aws_access_key
            os.environ['AWS_SECRET_ACCESS_KEY'] = aws_secret_key
            if aws_session_token:
                os.environ['AWS_SESSION_TOKEN'] = aws_session_token
        
        self.s3 = boto3.client('s3', region_name=region)
        self.bedrock = boto3.client('bedrock-runtime', region_name=region)
    
    def extract_pdf(self, bucket: str, pdf_key: str, output_dir: str = '.') -> str:
        """Extract PDF text and save to JSON"""
        print(f"📖 Extracting text from s3://{bucket}/{pdf_key}...")
        
        pdf_name = os.path.splitext(os.path.basename(pdf_key))[0]
        json_file = os.path.join(output_dir, f"{pdf_name}_pages.json")
        
        try:
            print("⏳ Downloading PDF...")
            response = self.s3.get_object(Bucket=bucket, Key=pdf_key)
            pdf_bytes = response['Body'].read()
            
            print("🖼️ Converting PDF to images...")
            images = convert_from_bytes(pdf_bytes)
            
            print(f"📄 Processing {len(images)} pages...")
            pages_dict = {}
            
            for page_num, image in enumerate(images, start=1):
                print(f"🔍 Page {page_num}...", end="", flush=True)
                
                buffered = BytesIO()
                image.save(buffered, format="PNG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                
                page_data = self._extract_text_from_image(img_base64)
                
                # Clean newlines from text - replace with period and space
                if 'text' in page_data and page_data['text']:
                    page_data['text'] = page_data['text'].replace('\n', '. ').strip()
                if 'summary' in page_data and page_data['summary']:
                    page_data['summary'] = page_data['summary'].replace('\n', '. ').strip()
                
                pages_dict[page_num] = page_data
                
                page_type = page_data.get('type', 'unknown')
                print(f" ✅ [{page_type}]")
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(pages_dict, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Saved to {json_file}")
            return json_file
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return ""
    
    def _extract_text_from_image(self, img_base64: str) -> Dict:
        """Extract text from image using vision models"""
        prompt = """This is a page from a children's storybook. Analyze and extract the text with categorization.

CATEGORIZATION RULES:
1. COVER PAGE (typically page 1): Type "cover" - extract title/author
2. BLANK PAGES: Type "blank" - no text needed
3. COMPREHENSION/ENGAGEMENT PAGES (typically at end): Type "comprehension" - extract questions
4. STORY PAGES: Type "story" - extract narrative text in reading order
5. NON-STORY CONTENT (copyright, publisher info): Type "ignore"

CRITICAL: READING ORDER FOR STORY PAGES
1. IDENTIFY THE MAIN SENTENCE FIRST - Look for primary narrative text
2. ARTISTIC/DECORATIVE WORDS - Words that rise, fall, curve are PART OF the main sentence
   - They belong WHERE THEY MAKE GRAMMATICAL SENSE, not where they appear visually
   - Example: "UP UP" rising + "It's going" = "It's going up up up"
3. READING FLOW - Read main sentence structure first, insert artistic words where they grammatically belong
4. COMMON PATTERNS - "going up up up" (up words may rise), "down down down" (down words may descend)

SUMMARY FOR STORY PAGES:
- Create child-friendly summary in under 25 words
- Use present tense and engaging words

RESPOND IN JSON FORMAT:
{"type": "story|cover|blank|comprehension|ignore", "text": "extracted text here", "summary": "brief summary under 25 words"}

Return ONLY valid JSON."""
        
        models = [
            ("us.amazon.nova-pro-v1:0", "nova"),
            ("anthropic.claude-3-5-sonnet-20241022-v2:0", "claude")
        ]
        
        for model_id, model_type in models:
            try:
                if model_type == "nova":
                    response = self.bedrock.invoke_model(
                        modelId=model_id,
                        body=json.dumps({
                            "messages": [{
                                "role": "user",
                                "content": [
                                    {"image": {"format": "png", "source": {"bytes": img_base64}}},
                                    {"text": prompt}
                                ]
                            }],
                            "inferenceConfig": {"max_new_tokens": 2000, "temperature": 0.05}
                        })
                    )
                    result = json.loads(response['body'].read())
                    return json.loads(result['output']['message']['content'][0]['text'].strip())
                else:
                    response = self.bedrock.invoke_model(
                        modelId=model_id,
                        body=json.dumps({
                            "anthropic_version": "bedrock-2023-05-31",
                            "max_tokens": 2000,
                            "messages": [{
                                "role": "user",
                                "content": [
                                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img_base64}},
                                    {"type": "text", "text": prompt}
                                ]
                            }]
                        })
                    )
                    result = json.loads(response['body'].read())
                    return json.loads(result['content'][0]['text'].strip())
            except:
                continue
        
        return {"type": "error", "text": "", "summary": ""}

def main():
    parser = argparse.ArgumentParser(description='Extract PDF text to JSON')
    parser.add_argument('--bucket', required=True, help='S3 bucket name')
    parser.add_argument('--pdf', required=True, help='PDF file name in S3')
    parser.add_argument('--output-dir', default='.', help='Output directory for JSON')
    parser.add_argument('--aws-key', help='AWS Access Key ID')
    parser.add_argument('--aws-secret', help='AWS Secret Access Key')
    parser.add_argument('--aws-session-token', help='AWS Session Token')
    
    args = parser.parse_args()
    
    extractor = PDFTextExtractor(
        aws_access_key=args.aws_key,
        aws_secret_key=args.aws_secret,
        aws_session_token=args.aws_session_token
    )
    
    json_file = extractor.extract_pdf(args.bucket, args.pdf, args.output_dir)
    
    if json_file:
        print(f"✅ Success! JSON file: {json_file}")
    else:
        print("❌ Failed to extract PDF")

if __name__ == "__main__":
    main()
