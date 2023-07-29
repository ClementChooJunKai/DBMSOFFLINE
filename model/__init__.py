import random
from flask_mysqldb import MySQL
from app import app
from flask import Flask, session, redirect, url_for, request
from helpers.database import *
from helpers.hashpass import *
from bson import json_util, ObjectId
from datetime import datetime
from utils import *
import json


# Create MySQL instance
mysql = MySQL(app)

@app.route('/login', methods=['POST'])
def checkloginusername():
    username = request.form["username"]
    check = db.user.find_one({"username": username})
    
    if check is None:
        return "No User"
    else:
      
        session['username'] = username  # Store the username in the session
        return redirect(url_for('index'))

def checkloginpassword():
    username = request.form["username"]
    check = db.user.find_one({"username": username})
    password = request.form["password"]
    otp = request.form["otp2"]
    hashpassword = getHashed(password)
    if hashpassword == check["password"] :
        #if otp == check["otp"]: add this code in to check for OTP we have disabled this to allow for testing

        session["username"] = username
        
        return "correct"
    else:
        return "wrong"

def checkusername():
    username = request.form["username"]
    check = db.user.find_one({"username": username})
    if check is None:
        return "Available"
    else:
        return "Username taken"


def registerUser():
    # Establish a connection to MySQL
    mysql_cursor = mysql.connection.cursor()

    fields = [k for k in request.form]
    values = [request.form[k] for k in request.form]
    data = dict(zip(fields, values))
    user_data = json.loads(json_util.dumps(data))
    user_data["password"] = getHashed(user_data["password"])
    user_data["confirmpassword"] = getHashed(user_data["confirmpassword"])
    user_data["created_at"] = datetime.now()
    db.user.insert_one(user_data)

    checkstoreid_query = "SELECT * FROM store WHERE storename = %s"
    mysql_cursor.execute(checkstoreid_query, (user_data["username"],))
    owndata = mysql_cursor.fetchall()
    maxstoreid_query = "SELECT max(storeid) FROM store"
    mysql_cursor.execute(maxstoreid_query)
    mstoreid = mysql_cursor.fetchall()
    print(mstoreid)
    maxstoreid = mstoreid[0][0] + 1
    if owndata:
        # Insert the owndata into the Account table
        account_query = "INSERT INTO Account (username, email, fullName, password, hashedPassword, storeid) VALUES (%s, %s, %s, %s, %s, %s)"
        account_values = (user_data["username"], user_data["email"], user_data["name"], user_data["password"], user_data["confirmpassword"], int(owndata[0][0]))
        mysql_cursor.execute(account_query, account_values)
    else:
        # Insert 0 as the owndata
        storedetail_query = "INSERT INTO Store (storeid, storeName, storeSlug, storeRating, storeAmtRating, productCount, storeFollowers, storeJoinedDate, chatPerformance, replyRate, platformType) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        store_values = (maxstoreid, user_data["username"], 'nil', 0, 0, 0, 0, '1 day ago', 0, 'within a few minutes', 'nil')
        mysql_cursor.execute(storedetail_query, store_values)
        account_query = "INSERT INTO Account (username, email, fullName, password, hashedPassword, storeId) VALUES (%s, %s, %s, %s, %s, %s)"
        account_values = (user_data["username"], user_data["email"], user_data["name"], user_data["password"], user_data["confirmpassword"], maxstoreid)
        mysql_cursor.execute(account_query, account_values)
      

    mysql_cursor.close()
    mysql.connection.commit()
    mysql.connection.close()

    # sendmail(subject="Registration for Flask Admin Boilerplate", sender="Flask Admin Boilerplate", recipient=user_data["email"], body="You successfully registered on Flask Admin Boilerplate")
    print("Done")