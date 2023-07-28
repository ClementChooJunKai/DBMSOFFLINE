from flask import Flask, Blueprint, render_template, request, redirect, url_for, session
from model import *
from utils import *

store_blueprint = Blueprint("store", __name__)

"""store_page Function - Store Listing Page
      Description:
        This function handles the "store.html" template, which displays a listing of stores available in the database.
        If the user is logged in, it retrieves the username from the session and establishes a connection to the database.
        The function then executes an SQL query to fetch store data, including storeID, storename, storejoineddate, platformtype, and watchlistId
        from the 'Store' table. Additionally, it performs a LEFT JOIN with the 'watchlist' table based on the storeID to get the watchlistId for each store.
        The fetched store data is processed to remove leading and trailing whitespaces (if any), and the results are stored in the 'stripped_data' variable.
        Finally, the database connection is closed, and the "store.html" template is rendered. If the user is logged in, the 'stripped_data' and 'username' are passed as context,
        allowing the template to display the store listing and the username. If the user is not logged in, the function returns the message "User not logged in."
"""


@store_blueprint.route("/store", methods=["GET"])
def store_page():
    if "username" in session:
        username = session["username"]

        cur = mysql.connection.cursor()
        # query = "SELECT storeID,storename,storejoineddate,platformtype FROM store;"
        query = "SELECT s.storeID, s.storename, s.storejoineddate, s.platformtype, w.watchlistId FROM Store s LEFT JOIN watchlist w ON s.storeID = w.watched_id"

        cur.execute(query)
        fetchdata = cur.fetchall()
        # stripped_data = [[str(item).strip() for item in row]
        #                  for row in fetchdata]
        stripped_data = [
            [str(item).strip() if item is not None else None for item in row]
            for row in fetchdata
        ]

        cur.close()
        return render_template(
            "store/store.html", data=stripped_data, username=username
        )
    else:
        return "User not logged in"


"""
                    compare Function - Compare Store's Composite Score
    Description: 
        This function handles the comparison of a store's composite score based on its various performance metrics.
        It retrieves the current user's username from the session and connects to the database.
        The function executes SQL queries to calculate the composite score and rank of each store.
        The composite score is calculated using different weighted metrics, including store rating, amount of rating, product count, store followers, and chat performance.
        The function fetches the composite score, ranking, store ID, and store name of the specified store from the database.
        Additionally, it fetches the user's own store data and calculates the composite score for comparison.
        The results are then displayed on the "compare.html" template for the user to compare the performance of the selected store with their own store and others.
"""
@store_blueprint.route("/compare/<int:store_id>", methods=["GET"])
def compare(store_id):
    username = session["username"]
    cur = mysql.connection.cursor()
    cur.execute(
        """
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
    """,
        (store_id,),
    )

    fetchdata = cur.fetchall()

    cur.execute(
        """
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
    """,
        (username,),
    )
    owndata = cur.fetchall()
    cur.execute("""SELECT * FROM Store WHERE storeId = %s;""", (store_id,))
    cstore = cur.fetchall()
    cur.execute("""SELECT * FROM Store WHERE storeName = %s;""", (username,))
    ownstore = cur.fetchall()

    return render_template(
        "store/compare.html",
        cstore=cstore,
        data=fetchdata,
        compscore=round(fetchdata[0][3], 3),
        storecomp=round(owndata[0][3], 3),
        storedata=owndata,
        selfdata=ownstore,
    )
