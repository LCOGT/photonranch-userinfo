import json
import os
import boto3
import decimal
from boto3.dynamodb.conditions import Key, Attr


dynamodb = boto3.resource('dynamodb')
user_info_table = os.environ['USER_INFO_TABLE']
# stage = os.environ['STAGE']


#=========================================#
#=======     Helper Functions     ========#
#=========================================#

def create_response(statusCode, message):
    """Returns a given status code."""

    return { 
        'statusCode': statusCode,
        'headers': {
            # Required for CORS support to work
            'Access-Control-Allow-Origin': '*',
            # Required for cookies, authorization headers with HTTPS
            'Access-Control-Allow-Credentials': 'true',
        },
        'body': message
    }

class DecimalEncoder(json.JSONEncoder):
    """Helper class to convert a DynamoDB item to JSON."""

    def default(self, o):
        if isinstance(o, set):
            return list(o)
        if isinstance(o, decimal.Decimal):
            if o % 1 != 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


#=========================================#
#=======       Core Methods       ========#
#=========================================#

def get_user_info(user_id, last_updated):
    """Retrieves full user info for a given user_id.
    
    Args: 
        user_id (str): ID of user
        last_updated (str): UTC ISO datetime of last edit

    Returns: 
        dict: contains the following keys:
            user_exists (bool): whether or not the user exists
            user_info (dict): full user info, including user_id,
            available_time, and last_updated
    """
    table = dynamodb.Table(user_info_table)

    response = table.get_item(
        Key={
            "user_id": user_id,
            "last_updated": last_updated
        }
    )

    if 'Item' in response:
        return {
            "user_exists": True,
            "user_info": response['Item']
        }
    else: 
        return {
            "user_exists": False,
            "user_info": []
        } 


#=========================================#
#=======    Handler Functions     ========#
#=========================================#

def user_info_handler(user_id, last_updated):
    """Retrieves full user info for a given user_id.
    
    Args: 
        user_id (str): ID of user
        last_updated (str): UTC ISO datetime of last edit

    Returns: 
        200 status code with full user info (JSON) if successful.
        Otherwise, 404 status code if user does not exist.
    """

    user_info = get_user_info(user_id, last_updated)

    # If the user exists, return their info
    if user_info["user_exists"]:
        user_info_json = json.dumps(user_info["user_info"], cls=DecimalEncoder)
        return create_response(200, user_info_json)
    else: 
        return create_response(404, "User not found.")


def update_user_info(event, context):
    """Updates non-restricted user information, intended for use by user.
    
    Args: 
        Event body with key value pairs of updated user info
        event.body.user_id (str, required): ID of user
        event.body.last_updated (str, required): UTC ISO datetime of last edit

    Returns: 
        200 status code with updated user info (JSON) if successful.
        Otherwise, 404 status code if user does not exist or 403 status code if
        user tries to update time_amount
    
    """

    table = dynamodb.Table(user_info_table)

    event_body = json.loads(event.get("body", ""))
    
    user_id = event_body["user_id"]
    last_updated = event_body["last_updated"]

    old_user_info = get_user_info(user_id, last_updated)

    # If the user doesn't exist:
    if not old_user_info["user_exists"]:
        return create_response(404, "User not found.")

    # Initialize the dict that will overwrite the existing user info.
    updated_user_info = old_user_info["user_info"]

    # Iterate over the attributes to update, excluding time_amount
    for key in event_body:
        if not key == "time_amount":
            updated_user_info[key] = event_body[key]
        else:
            return create_response(403, "Cannot update time_amount. Please use /add-time or /deduct-time.")

    # Delete the existing user info from the table
    table.delete_item(
        Key={
            "user_id": user_id,
            "last_updated": last_updated
        },
    )

    # Add the updated user info back
    dynamodb_entry = json.loads(json.dumps(updated_user_info, cls=DecimalEncoder), parse_float=decimal.Decimal)
    table_response = table.put_item(Item=dynamodb_entry)
    
    return create_response(200, table_response)


def add_time(event, context):
    """Adds time to a user's allocation. Must be authenticated.

    TODO: Args and function might need to change depending on how moodle 
    handles dates and how it can pass info to an endpoint (might only be 
    query parameters). This is why add_time is separate from updating user
    info in general and why it's separate from removing time, along with
    different level of authentication.

    Args: 
        event.body.user_id (str): ID of user
        event.body.time_amount (int): time in minutes to add
        event.body.last_updated (str): UTC ISO datetime of last edit

    Returns: 
        200 status code with updated user info (JSON) if successful.
        Otherwise, 404 status code if user does not exist.
    """

    table = dynamodb.Table(user_info_table)

    event_body = json.loads(event.get("body", ""))
    
    user_id = event_body["user_id"]
    last_updated = event_body["last_updated"]
    time_amount = event_body["time_amount"]

    old_user_info = get_user_info(user_id, last_updated)

    # somewhere in here goes authorization

    # If the user doesn't exist:
    if not old_user_info["user_exists"]:
        return create_response(404, "User not found.")

    # Initialize the dict that will overwrite the existing user info.
    updated_user_info = old_user_info["user_info"]

    # Make the changes needed:
    updated_user_info["last_updated"] = last_updated

    # Add to the time if the user already has some
    try:
        updated_user_info["available_time"] += time_amount
    except:
        updated_user_info["available_time"] = time_amount

    # Delete the existing user info from the table
    table.delete_item(
        Key={
            "user_id": user_id,
            "last_updated": last_updated
        },
    )

    # Add the updated user info back
    dynamodb_entry = json.loads(json.dumps(updated_user_info, cls=DecimalEncoder), parse_float=decimal.Decimal)
    table_response = table.put_item(Item=dynamodb_entry)
    
    return create_response(200, table_response)


def deduct_time(event, context):
    """Removes time from a user's allocation, meant to be performed after observing.
    Must be authenticated, and that authentication may be different than adding time.

    Args: 
        event.body.user_id (str): ID of user
        event.body.time_amount (int): time in minutes to subtract
        event.body.last_updated (str): UTC ISO datetime of last edit

    Returns: 
        200 status code with updated user info (JSON) if successful.
        Otherwise, 404 status code if user does not exist.
    """

    table = dynamodb.Table(user_info_table)

    event_body = json.loads(event.get("body", ""))
    
    user_id = event_body["user_id"]
    last_updated = event_body["last_updated"]
    time_amount = event_body["time_amount"]

    old_user_info = get_user_info(user_id, last_updated)

    # somewhere in here goes authorization, but different from the above?

    # If the user doesn't exist:
    if not old_user_info["user_exists"]:
        return create_response(404, "User not found.")

    # Initialize the dict that will overwrite the existing user info.
    updated_user_info = old_user_info["user_info"]

    # Make the changes needed:
    updated_user_info["last_updated"] = last_updated

    # Add to the time if the user already has some
    try:
        # Throw an error if time amount requested exceeds available time
        # (might need to change this depending on how it's implemented in the frontend)
        if time_amount > updated_user_info["available_time"]:
            return create_response(400, "Not enough available time.")

        updated_user_info["available_time"] -= time_amount

    except:
        return create_response(400, "Not enough available time.")

    # Delete the existing user info from the table
    table.delete_item(
        Key={
            "user_id": user_id,
            "last_updated": last_updated
        },
    )

    # Add the updated user info back
    dynamodb_entry = json.loads(json.dumps(updated_user_info, cls=DecimalEncoder), parse_float=decimal.Decimal)
    table_response = table.put_item(Item=dynamodb_entry)
    
    return create_response(200, table_response)