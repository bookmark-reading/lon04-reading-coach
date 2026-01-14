"""
Lambda PDF Text Extraction
Triggered by S3 upload via EventBridge, extracts text from PDF and saves JSON to S3
"""

import boto3
import json
import base64
from typing import Dict
from pdf2image import convert_from_bytes
from io import BytesIO

s3 = boto3.client('s3')
bedrock = boto3.client('bedrock-runtime', region_name='us-west-2')

def extract_text_from_image(img_base64: str) -> Dict:
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
                response = bedrock.invoke_model(
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
                response = bedrock.invoke_model(
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

def lambda_handler(event, context):
    """Lambda handler triggered by EventBridge on S3 upload"""
    try:
        # Extract S3 details from EventBridge event
        detail = event['detail']
        bucket = detail['bucket']['name']
        pdf_key = detail['object']['key']
        
        # Only process PDF files
        if not pdf_key.lower().endswith('.pdf'):
            return {'statusCode': 200, 'body': 'Not a PDF file, skipping'}
        
        print(f"Processing s3://{bucket}/{pdf_key}")
        
        # Download PDF
        response = s3.get_object(Bucket=bucket, Key=pdf_key)
        pdf_bytes = response['Body'].read()
        
        # Convert to images
        images = convert_from_bytes(pdf_bytes)
        print(f"Processing {len(images)} pages")
        
        # Extract text from each page
        pages_dict = {}
        for page_num, image in enumerate(images, start=1):
            print(f"Page {page_num}...")
            
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            page_data = extract_text_from_image(img_base64)
            
            # Clean newlines
            if 'text' in page_data and page_data['text']:
                page_data['text'] = page_data['text'].replace('\n', '. ').strip()
            if 'summary' in page_data and page_data['summary']:
                page_data['summary'] = page_data['summary'].replace('\n', '. ').strip()
            
            pages_dict[page_num] = page_data
        
        # Save JSON to S3 (same bucket, replace .pdf with .json)
        json_key = pdf_key.replace('.pdf', '.json')
        s3.put_object(
            Bucket=bucket,
            Key=json_key,
            Body=json.dumps(pages_dict, indent=2, ensure_ascii=False),
            ContentType='application/json'
        )
        
        print(f"Saved to s3://{bucket}/{json_key}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Success',
                'pdf': pdf_key,
                'json': json_key,
                'pages': len(pages_dict)
            })
        }
        
    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
