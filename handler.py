import json


def getAvailableTime(event, context):
    """Retrieves time allocation available to a list of users.
    (List in case we start wanting to use groups at some point, so 
    a teacher could access that?)
    
    Args: list of userids

    Returns: time allocation, when time allocation was last updated
    """

    #pull info from dynamoDB

def addTime(event, context):
    """Adds time to a user's allocation. Must be authenticated.

    Args: userid, time amount, (anything needed for auth?)

    Returns: changes time in dynamoDB, also changes last updated time
    """

    #pull info from dynamoDB 
    #if userid not in there, add it to the table 
    #check auth
    #add time
    #change last updated time

def deductTime(event, context):
    """Removes time from a user's allocation. Must be authenticated
    Seperate from adding time for different auth purposes??

    Args: userid, time amount, (anything needed for auth?)

    Returns: changes time in dynamoDB, also changes last updated time
    """

    #pull info from dynamoDB 
    #check auth
    #remove time
    #change last updated time