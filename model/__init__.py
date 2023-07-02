from flask_mysqldb import MySQL
from App import app
from flask import Flask, session, redirect, url_for, request
from helpers.database import *
from helpers.hashpass import *
from bson import json_util, ObjectId
from datetime import datetime

import json


# Configure MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'dbms'

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
    hashpassword = getHashed(password)
    if hashpassword == check["password"]:
        # sendmail(subject="Login on Flask Admin Boilerplate", sender="Flask Admin Boilerplate", recipient=check["email"], body="You successfully logged in on Flask Admin Boilerplate")
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


    account_query = "INSERT INTO Account ( username, email, fullName, password,hashedPassword) VALUES (%s, %s, %s, %s,%s)"
    account_values = ( user_data["username"], user_data["email"], user_data["name"],user_data["password"], user_data["confirmpassword"])
    mysql_cursor.execute(account_query, account_values)
    
    mysql_cursor.close()
    mysql.connection.commit()
    mysql.connection.close()

    # sendmail(subject="Registration for Flask Admin Boilerplate", sender="Flask Admin Boilerplate", recipient=user_data["email"], body="You successfully registered on Flask Admin Boilerplate")
    print("Done")