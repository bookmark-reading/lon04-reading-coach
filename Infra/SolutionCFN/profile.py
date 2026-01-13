# profile.py
#
# GET  /profile -> returns the DynamoDB item for the current user
# PUT  /profile -> overwrites the DynamoDB item for the current user
#
# Identity:
# - userId is taken from JWT claim "sub" (Cognito user unique id)

import json
import os
import boto3

USER_TABLE = os.environ["USER_TABLE"]
ddb = boto3.resource("dynamodb")
table = ddb.Table(USER_TABLE)


def _claims(event) -> dict:
    # HttpApi + JWT authorizer places claims under requestContext.authorizer.jwt.claims
    rc = event.get("requestContext") or {}
    auth = rc.get("authorizer") or {}
    jwt = auth.get("jwt") or {}
    return jwt.get("claims") or {}


def _user_id(event) -> str | None:
    return _claims(event).get("sub")


def _json(status: int, payload: dict):
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(payload),
    }


def handler(event, context):
    try:
        user_id = _user_id(event)
        if not user_id:
            return {"statusCode": 401, "body": "Unauthorized"}

        method = (event.get("requestContext") or {}).get("http", {}).get("method", "")

        if method == "GET":
            res = table.get_item(Key={"userId": user_id})
            item = res.get("Item") or {"userId": user_id}
            return _json(200, item)

        if method == "PUT":
            body = json.loads(event.get("body") or "{}")

            # MVP: store exactly the profile fields we care about
            item = {
                "userId": user_id,
                "firstName": body.get("firstName"),
                "lastName": body.get("lastName"),
                "grade": body.get("grade"),
            }

            table.put_item(Item=item)
            return _json(200, item)

        return {"statusCode": 405, "body": "Method Not Allowed"}

    except Exception as e:
        print(e)
        return {"statusCode": 500, "body": "Internal Server Error"}
