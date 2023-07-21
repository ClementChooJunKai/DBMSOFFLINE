from flask import Flask, Blueprint, render_template, request, redirect, url_for, session
from model import *
from utils import *

store_blueprint = Blueprint('store', __name__)

@store_blueprint.route('/store',  methods=["GET"])
def store_page():
    if 'username' in session:
        username = session['username']

        cur = mysql.connection.cursor()
        #query = "SELECT storeID,storename,storejoineddate,platformtype FROM store;"
        query = "SELECT s.storeID, s.storename, s.storejoineddate, s.platformtype, w.watchlistId FROM Store s LEFT JOIN watchlist w ON s.storeID = w.watched_id"
        
        cur.execute(query)
        fetchdata = cur.fetchall()
        # stripped_data = [[str(item).strip() for item in row]
        #                  for row in fetchdata]
        stripped_data = [[str(item).strip() if item is not None else None for item in row]
                    for row in fetchdata]
        
        cur.close()
        return render_template("store/store.html", data=stripped_data, username=username)
    else:
        return "User not logged in"



@store_blueprint.route('/compare/<int:store_id>', methods=['GET'])
def compare(store_id):
    username = session['username']
    cur = mysql.connection.cursor()
    cur.execute('''
        SELECT
          ranking,
          storeId,
          storeName,
          compositeScore
          
        FROM (
          SELECT
            storeId,
            storeName,
            compositeScore,
            RANK() OVER (ORDER BY compositeScore DESC) AS ranking
          FROM (
            SELECT
              storeId,
              storeName,
              (
                (storeRating / 5) * 0.5 +
                (storeAmtRating / max_storeAmtRating) * 0.1 +
                (productCount / max_productCount) * 0.15 +
                (storeFollowers / max_storeFollowers) * 0.15 +
                (chatPerformance ) * 0.1 
            
              ) AS compositeScore
            FROM Store,
              (SELECT
                MAX(storeAmtRating) AS max_storeAmtRating,
                MAX(productCount) AS max_productCount,
                MAX(storeFollowers) AS max_storeFollowers
              FROM Store) AS max_values
          ) AS ranked_shops
        ) AS ranked_stores
        WHERE storeId = %s;
    ''', (store_id,))

    fetchdata = cur.fetchall()

    cur.execute('''
        SELECT
          ranking,
          storeId,
          storeName,
          compositeScore
        FROM (
          SELECT
            storeId,
            storeName,
            compositeScore,
            RANK() OVER (ORDER BY compositeScore DESC) AS ranking
          FROM (
            SELECT
              storeId,
              storeName,
              (
                (storeRating / 5) * 0.5 +
                (storeAmtRating / max_storeAmtRating) * 0.1 +
                (productCount / max_productCount) * 0.15 +
                (storeFollowers / max_storeFollowers) * 0.15 +
                (chatPerformance ) * 0.1 
            
              ) AS compositeScore
            FROM Store,
              (SELECT
                MAX(storeAmtRating) AS max_storeAmtRating,
                MAX(productCount) AS max_productCount,
                MAX(storeFollowers) AS max_storeFollowers
              FROM Store) AS max_values
          ) AS ranked_shops
        ) AS ranked_stores
        WHERE storeName = %s;
    ''', (username,))
    owndata = cur.fetchall()
    cur.execute('''SELECT * FROM Store WHERE storeId = %s;''', (store_id,))
    cstore = cur.fetchall()
    cur.execute('''SELECT * FROM Store WHERE storeName = %s;''', (username,))
    ownstore = cur.fetchall()

    return render_template("store/compare.html", cstore=cstore, data=fetchdata, compscore=round(fetchdata[0][3], 3), storecomp=round(owndata[0][3], 3), storedata=owndata, selfdata=ownstore)