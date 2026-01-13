# list_books.py
#
# GET /books
# - Loads the user's profile to get grade
# - Queries Books table GradeIndex by grade
#
# Assumes Books table has GSI:
# - IndexName: GradeIndex
# - Partition key: grade (Number)

import json
import os
import boto3
from boto3.dynamodb.conditions import Key

USER_TABLE = os.environ["USER_TABLE"]
BOOKS_TABLE = os.environ["BOOKS_TABLE"]
BOOKS_GSI = os.environ.get("BOOKS_GSI", "GradeIndex")

ddb = boto3.resource("dynamodb")
user_table = ddb.Table(USER_TABLE)
books_table = ddb.Table(BOOKS_TABLE)


def _claims(event) -> dict:
    rc = event.get("requestContext") or {}
    auth = rc.get("authorizer") or {}
    jwt = auth.get("jwt") or {}
    return jwt.get("claims") or {}


def _user_id(event) -> str | None:
    return _claims(event).get("sub")


def handler(event, context):
    try:
        user_id = _user_id(event)
        if not user_id:
            return {"statusCode": 401, "body": "Unauthorized"}

        # Grade is stored in user profile (not a key; just an attribute)
        profile = user_table.get_item(Key={"userId": user_id}).get("Item") or {}
        grade = profile.get("grade")
        if grade is None:
            return {"statusCode": 400, "body": "User profile is missing grade"}

        # Query books by grade; sorting within grade depends on your GSI sort key
        res = books_table.query(
            IndexName=BOOKS_GSI,
            KeyConditionExpression=Key("grade").eq(grade),
        )

        return {
            "statusCode": 200,
            "headers": {"content-type": "application/json"},
            "body": json.dumps(res.get("Items") or []),
        }

    except Exception as e:
        print(e)
        return {"statusCode": 500, "body": "Internal Server Error"}
