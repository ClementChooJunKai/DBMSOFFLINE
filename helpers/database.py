import pymongo

client = pymongo.MongoClient("mongodb://localhost:27017/")

db = client["userData"]
collection = db["user"]


# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

# db = client["UserData"]

