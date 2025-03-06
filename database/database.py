import pymongo, os
from config import DB_URL, DB_NAME

dbclient = pymongo.MongoClient(DB_URL)
database = dbclient[DB_NAME]
user_data = database['users']
join_requests = database['join_requests']  # नया कलेक्शन Join Requests स्टोर करने के लिए

async def present_user(user_id: int):
    """ चेक करें कि यूज़र डेटाबेस में मौजूद है या नहीं """
    found = user_data.find_one({'_id': user_id})
    return bool(found)

async def add_user(user_id: int):
    """ नया यूज़र डेटाबेस में जोड़ें """
    user_data.insert_one({'_id': user_id})
    return

async def full_userbase():
    """ सभी यूज़र आईडी लिस्ट के रूप में प्राप्त करें """
    user_docs = user_data.find()
    return [doc['_id'] for doc in user_docs]

async def del_user(user_id: int):
    """ यूज़र को डेटाबेस से हटाएं """
    user_data.delete_one({'_id': user_id})
    return

# 🔹🔹 Join Request Handling Functions 🔹🔹

async def find_join_req(user_id: int):
    """ चेक करें कि यूज़र ने request भेजी है या नहीं """
    found = join_requests.find_one({'user_id': user_id})
    return bool(found)

async def add_join_req(user_id: int):
    """ यूज़र की Join Request को डेटाबेस में सेव करें """
    join_requests.insert_one({'user_id': user_id})
    return

async def del_join_req():
    """ सभी Join Requests को हटाएं """
    join_requests.delete_many({})
    return
