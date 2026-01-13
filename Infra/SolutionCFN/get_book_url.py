# get_book_url.py
#
# GET /books/{bookId}/url
# - Loads Books table item by bookId (expects s3Key in the item)
# - Returns presigned S3 GET URL valid for 1 hour

import json
import os
import boto3

BOOKS_BUCKET = os.environ["BOOKS_BUCKET"]
BOOKS_TABLE = os.environ["BOOKS_TABLE"]
TTL = int(os.environ.get("URL_TTL_SECONDS", "3600"))

ddb = boto3.resource("dynamodb")
books_table = ddb.Table(BOOKS_TABLE)
s3 = boto3.client("s3")


def handler(event, context):
    try:
        path_params = event.get("pathParameters") or {}
        book_id = path_params.get("bookId")
        if not book_id:
            return {"statusCode": 400, "body": "Missing bookId"}

        # Book item should include: s3Key (path/key to PDF in BooksBucket)
        item = books_table.get_item(Key={"bookId": book_id}).get("Item")
        if not item or not item.get("s3Key"):
            return {"statusCode": 404, "body": "Book not found"}

        url = s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": BOOKS_BUCKET, "Key": item["s3Key"]},
            ExpiresIn=TTL,
        )

        return {
            "statusCode": 200,
            "headers": {"content-type": "application/json"},
            "body": json.dumps({"url": url, "expiresInSeconds": TTL}),
        }

    except Exception as e:
        print(e)
        return {"statusCode": 500, "body": "Internal Server Error"}
