from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
from model import *
from utils import *
from pages.revenue import revenue_blueprint
from pages.products import products_blueprint
from pages.store import store_blueprint
from pages.category import category_blueprint
from decimal import Decimal
import re
from flask_mail import Mail, Message


app = Flask(__name__)
app = configure_app(app)
app.register_blueprint(revenue_blueprint)
app.register_blueprint(products_blueprint)
app.register_blueprint(store_blueprint)
app.register_blueprint(category_blueprint)


# Create MySQL instance
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "tay.jiale@gmail.com"
app.config["MAIL_PASSWORD"] = "tfclioagsaftodjo"
mail = Mail(app)
mysql.init_app(app)


@app.route("/", methods=["GET", "POST"])
def home():
    # Retrieve all data from the "store" table where the "storename" matches the given parameter.
    storeDataquery = "SELECT * FROM store WHERE storename = %s;"

    # Count the number of products associated with a specific store.
    productcount_query = "SELECT COUNT(*) FROM product p INNER JOIN store s ON p.storeid = s.storeid WHERE storename = %s;"

    # Calculate the total earnings of each store by multiplying the quantity sold of each product with its discounted price.
    # Group the results by store name, order them in descending order based on total earnings, and retrieve only the top 'LIMIT' number of records.
    top_earnings_query = """
        SELECT s.storename, SUM(p.quantitysold * p.discountedprice) AS total_earnings
        FROM product AS p
        INNER JOIN store AS s ON p.storeid = s.storeid
        GROUP BY s.storename
        ORDER BY total_earnings DESC
        LIMIT %s;
    """

    # Calculate the total earnings of each store similar to 'top_earnings_query', but order the results in ascending order based on total earnings.
    # This will give the stores with the lowest earnings.
    bottom_earnings_query = """
        SELECT s.storename, SUM(p.quantitysold * p.discountedprice) AS total_earnings
        FROM product AS p
        INNER JOIN store AS s ON p.storeid = s.storeid
        GROUP BY s.storename
        ORDER BY total_earnings ASC
        LIMIT %s;
    """

    # Calculate the total earnings of a specific store by multiplying the quantity sold of each product with its discounted price.
    # Filter the results to consider only the store specified by the given "storename."
    earnings_query = """
        SELECT SUM(p.quantitysold * p.discountedprice) AS total_earnings
        FROM product AS p
        INNER JOIN store AS s ON p.storeid = s.storeid
        WHERE s.storename = %s;
    """

    # Calculate the rating difference between a specific store and the average rating of all other stores.
    # Retrieve the "storename" and the difference between the store's "storerating" and the average rating calculated over all other stores
    # (excluding the store specified by the given "storename").
    rating_difference_query = """
        SELECT storename, storerating - avg_rating AS rating_difference
        FROM (
            SELECT s.storename, s.storerating, AVG(s2.storerating) AS avg_rating
            FROM store AS s
            INNER JOIN store AS s2 ON s.storename != s2.storename
            WHERE s.storename = %s
            GROUP BY s.storename, s.storerating
        ) AS subquery;
    """

    # Retrieve data from the "Store" and "watchlist" tables.
    # Select the store's "storeId," "storeName," "storejoineddate," "platformtype," and the "watchlistId" associated with the store
    # where the "storeId" matches the given parameter.
    query_retrieve_watch_store = """
        SELECT s.storeId, s.storeName, s.storejoineddate, s.platformtype, w.watchlistId FROM Store s 
        INNER JOIN watchlist w 
        ON s.storeId = w.watched_id
        WHERE w.storeId = %s
    """

    # Retrieve data from the "product" and "watchlist" tables.
    # Select the product's "productid," "ProductName," "Productdesc," "sellingprice," "discountedprice," "category," "quantitysold,"
    # "productlikes," "productratings," "productratingsamt," "shippingtype," and "shipfrom," along with the "watchlistId" associated with the product.
    # The query is filtered to consider only products belonging to the store specified by the given "storeId" and having "watched_type" as 'product'.
    query_retrieve_watch_product = """
        SELECT p.productid, p.ProductName, p.Productdesc, p.sellingprice, p.discountedprice, p.category, p.quantitysold, p.productlikes, 
            p.productratings, p.productratingsamt, p.shippingtype, p.shipfrom, w.watchlistId
        FROM product p
        INNER JOIN watchlist w 
        ON p.productid = w.watched_id
        WHERE w.storeId = %s AND w.watched_type ='product'
    """
    # Count the number of products associated with a specific store.
    # This query uses an INNER JOIN between the "product" and "store" tables based on the "storeid" column.
    # It filters the results by the given "storename" to consider only products related to the specified store.
    productcount_query = "SELECT COUNT(*) FROM product p INNER JOIN store s ON p.storeid = s.storeid WHERE storename = %s;"

    """
    Handles a POST request from the client and performs various database queries to retrieve and calculate data related to the user's store.
    Retrieves store information, product count, earnings, and rating difference compared to other stores.
    Allows the user to choose between top-earning or bottom-earning stores and set the number of shops to display.
    Executes appropriate MySQL queries to fetch store and product data based on user's selection.
    Also retrieves information about the stores and products watched by the user's store.
    Once all data is collected, renders the "index.html" template with the fetched data and variables for client-side display.
    Note: Assumes a valid user session with "username" stored in it. Proper user authentication and session management are crucial for security and correctness of the application.
    This is the post method for the dashboard page.
    """
    if request.method == "POST":
        # Check if "username" exists in the session, meaning the user is logged in.
        if "username" in session:
            # Set a default value for "shop_count" (it's set to 2 in this case).
            shop_count = 2

            # Get the "username" from the session.
            username = session["username"]

            # Create a cursor object to execute MySQL queries.
            cur = mysql.connection.cursor()

            # Execute "storeDataquery" to fetch store data for the logged-in user.
            cur.execute(storeDataquery, (username,))
            fetchdata = cur.fetchall()

            # Execute "productcount_query" to get the number of products associated with the user's store.
            cur.execute(productcount_query, (username,))
            productcount_data = cur.fetchone()
            productcount = productcount_data[0]

            # Get the value of "shopSelection" from the form (user's choice for top or bottom shops) and "shopCount" (number of shops to display).
            shop_selection = request.form.get("shopSelection")
            shop_count = int(request.form.get("shopCount"))

            # Initialize lists for earnings data and bottom earnings data.
            earning = []  # Initialize with an empty list
            bottom_earnings_data = []  # Initialize with an empty list

            # Depending on the user's choice (top or bottom), execute corresponding query to get earnings data for the shops.
            if shop_selection == "top":
                cur.execute(top_earnings_query, (shop_count,))
                earnings_data = cur.fetchall()
                # Create a list of tuples for the top earning shops with their store name and total earnings.
                earning = [
                    (storename, float(total_earnings))
                    for storename, total_earnings in earnings_data
                ]
            elif shop_selection == "bottom":
                cur.execute(bottom_earnings_query, (shop_count,))
                bottom_earnings_data = cur.fetchall()
            else:
                earning = []

            # Execute "earnings_query" to get the total earnings of the user's store.
            cur.execute(earnings_query, (username,))
            earnings_data = cur.fetchone()
            # Extract the total earnings value from the query result, or set it to 0 if it's None.
            total_earnings = earnings_data[0] if earnings_data[0] is not None else 0

            # Execute "rating_difference_query" to get the rating difference of the user's store compared to the average rating of other stores.
            cur.execute(rating_difference_query, (username,))
            rating_difference_data = cur.fetchone()
            # Extract the rating difference value from the query result, or set it to 0 if it's None.
            rating_difference = (
                rating_difference_data[1] if rating_difference_data is not None else 0
            )

            # Determine if the user's store rating is above or below average and construct a message.
            if rating_difference >= 0:
                rdiff = "You are above average by: " + str(round(rating_difference, 2))
            else:
                rdiff = "You are below average by: " + str(
                    round(rating_difference, 2)
                ).strip("-")

            # If "fetchdata" is not empty, extract the "store_id" from the first tuple in the result.
            if fetchdata:
                first_tuple = fetchdata[0]
                store_id = first_tuple[0]

            # Execute "query_retrieve_watch_store" to retrieve data about stores watched by the user's store.
            cur.execute(query_retrieve_watch_store, (store_id,))
            watch_store = cur.fetchall()

            # Execute "query_retrieve_watch_product" to retrieve data about products watched by the user's store.
            cur.execute(query_retrieve_watch_product, (store_id,))
            watch_product = cur.fetchall()

            # Count the number of watched products.
            count = 0
            for row in watch_product:
                count += 1
                print(count)

            # Close the cursor after executing the queries.
            cur.close()

            # Render the "index.html" template with the retrieved data and variables.
            return render_template(
                "index.html",
                username=username,
                productcount=productcount,
                data=fetchdata,
                performance=int(fetchdata[0][8] * 100),
                earning=earning,
                bottom_earnings_data=bottom_earnings_data,
                difference=rdiff,
                watch_store=watch_store,
                watch_product=watch_product,
            )

    # This is the view function for the 'index' page, which is accessed by the URL '/'
    # It handles the 'GET' method .
    # For the 'GET' request, it retrieves data from the database and renders the 'index.html' template.

    
    if "username" in session:
        # If the user is logged in, retrieve their username from the session
        username = session["username"]
        
        # Get all data from the store table for the logged-in user
        cur = mysql.connection.cursor()
        cur.execute(storeDataquery, (username,))
        fetchdata = cur.fetchall()

        # Get the total count of products for the logged-in user
        cur.execute(productcount_query, (username,))
        productcount_data = cur.fetchone()
        productcount = productcount_data[0]

        # Get the total earnings for the logged-in user
        cur.execute(earnings_query, (username,))
        earnings_data = cur.fetchone()
        total_earnings = earnings_data[0] if earnings_data[0] is not None else 0

        # Get the rating difference for the logged-in user
        cur.execute(rating_difference_query, (username,))
        rating_difference_data = cur.fetchone()
        rating_difference = rating_difference_data[1] if rating_difference_data is not None else 0

        # Create a message based on the rating difference
        if rating_difference >= 0:
            rdiff = "You are above average by: " + str(round(rating_difference, 2))
        else:
            rdiff = "You are below average by: " + str(round(rating_difference, 2)).strip("-")

        # If there is data in fetchdata, get the store_id from the first tuple
        if fetchdata:
            first_tuple = fetchdata[0]
            store_id = first_tuple[0]

        # Retrieve data for watched stores and watched products for the logged-in user
        cur.execute(query_retrieve_watch_store, (store_id,))
        watch_store = cur.fetchall()

        cur.execute(query_retrieve_watch_product, (store_id,))
        watch_product = cur.fetchall()

        # Count the number of rows in watch_product
        count = 0
        for row in watch_product:
            count += 1

        cur.close()

        # Render the 'index.html' template with the retrieved data and variables
        return render_template(
            "index.html",
            username=username,
            data=fetchdata,
            productcount=productcount,
            performance=int(fetchdata[0][8] * 100),
            difference=rdiff,
            watch_store=watch_store,
            watch_product=watch_product,
        )
    else:
        # If the user is not logged in, render the 'login.html' template
        return render_template("login.html")



@app.route("/generateotp", methods=["GET", "POST"])
def generateotp():
    if request.method == "POST":
        otp_username = request.form.get("username")
        print(otp_username)

        # Find the user in the database based on the provided username
        check = db.user.find_one({"username": otp_username})

        # Generate a random 6-digit password (OTP)
        otp = str(random.randint(100000, 999999))

        # Get the recipient's email from the user's database record
        recipient_email = check["email"]
        print(recipient_email)

        # Create a message containing the OTP and send it to the user's email
        msg = Message(
            "2FA Verification Code",
            sender="your-email@example.com",  # Replace with your valid email address
            recipients=[recipient_email],
        )
        msg.body = f"Your verification code is: {otp}"
        mail.send(msg)

        # Store the generated OTP in the session for verification later
        session["otp"] = otp

        # Return the OTP to the caller (for debugging or other purposes)
        return otp

    else:
        # If the request method is not POST, render the login form
        return render_template("login.html")


@app.route("/validateotp", methods=["POST"])
def validate_otp():
    user_entered_otp = request.form.get("otp")  # Get the OTP submitted by the user

    if user_entered_otp == session["otp"]:
        return jsonify({"result": "success"})  # OTP is correct
    else:
        return jsonify({"result": "error"})  # OTP is incorrect


@app.route("/success")
def success():
    return render_template("success.html")


@app.route("/index")
def dash():
    return render_template("index.html")


@app.route("/", methods=["GET"])
def login_page():
    if "username" in session:
        return render_template("index.html")
    else:
        return render_template("login.html")


# Register new user


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    elif request.method == "POST":
        registerUser()
        return redirect(url_for("login"))


# Check if email already exists in the registration page


@app.route("/checkusername", methods=["POST"])
def check_username():
    return checkusername()


# Everything Login (Routes to render page, check if username exists, and also verify password through Jquery AJAX request)


@app.route("/login", methods=["GET"])
def login():
    if request.method == "GET":
        if "username" not in session:
            return render_template("login.html")
        else:
            return redirect(url_for("home"))


# Check if username exists


@app.route("/checkloginusername", methods=["POST"])
def check_login_username():
    return checkloginusername()


# Check if password is correct


@app.route("/checkloginpassword", methods=["POST"])
def check_login_password():
    return checkloginpassword()


# The admin logout


@app.route("/logout", methods=["GET"])
def logout():
    session.pop("username", None)  # remove user session
    return redirect(url_for("home"))  # redirect to home page with message


# Forgot Password


@app.route("/forgot-password", methods=["GET"])
def forgot_password():
    return render_template("forgot-password.html")


# 404 Page


@app.route("/404", methods=["GET"])
def error_page():
    return render_template("404.html")


# Blank Page


@app.route("/blank", methods=["GET"])
def blank():
    return render_template("blank.html")


# Blank Page


@app.route("/profile", methods=["GET"])
def settings():
    if "username" in session:
        username = session["username"]

        cur = mysql.connection.cursor()

        # Execute the SQL query to retrieve all data from the "account" table
        query = "SELECT * FROM account where username = %s;"
        cur.execute(
            query, (username,)
        )  # Pass username as a tuple with a single element

        # Fetch all the rows
        all_accounts = cur.fetchall()

        # Close the cursor and the database connection
        cur.close()

        return render_template(
            "profile.html", username=username, user_data=all_accounts
        )


# Update Profile
@app.route("/update_profile", methods=["POST"])
def update_profile():
    if "username" in session:
        # Get the values from the submitted form
        full_name = request.form.get("name")
        email = request.form.get("email")
        phone_number = request.form.get("phone")
        address = request.form.get("address")
        username = session["username"]

        # Update the profile in the database
        cur = mysql.connection.cursor()
        update_query = "UPDATE account SET fullname = %s, email = %s, phonenumber = %s, address = %s WHERE username = %s"
        cur.execute(update_query, (full_name, email, phone_number, address, username))
        mysql.connection.commit()
        cur.close()

        # Redirect the user back to the profile page
        return render_template("success.html")

# Change Password 
@app.route("/change-password", methods=["POST"])
def change_password():
    if "username" in session:
        username = session["username"]

        cur = mysql.connection.cursor()

        # Execute the SQL query to retrieve all data from the "account" table
        query = "SELECT * FROM account where username = %s;"
        cur.execute(
            query, (username,)
        )  # Pass username as a tuple with a single element
        # Fetch all the rows
        all_accounts = cur.fetchall()
        # Close the cursor and the database connection

        current_password = request.form.get("currentPassword")
        new_password = request.form.get("newPassword")
        confirm_password = request.form.get("confirmPassword")

        # Retrieve the user data from MongoDB
        user_data = db.user.find_one({"username": username})

        # Check if the current password matches the stored password
        hashed_current_password = getHashed(
            current_password
        )  # Use your existing getHashed method
        if hashed_current_password == user_data["password"]:
            # Hash the new password using your existing getHashed method
            hashed_new_password = getHashed(new_password)

            # Update the new password in MongoDB
            db.user.update_one(
                {"username": username}, {"$set": {"password": hashed_new_password}}
            )

            # Update the new password in SQL
            update_query = "UPDATE account SET hashedpassword = %s, password = %s WHERE username = %s"
            cur.execute(
                update_query, (hashed_new_password, hashed_new_password, username)
            )
            mysql.connection.commit()
            cur.close()

            # Pass a success message to the template
            return render_template(
                "success.html", message="Password changed successfully."
            )
        else:
            # Current password does not match, pass an error message to the template
            return render_template(
                "profile.html",
                error="Current password is incorrect.",
                user_data=all_accounts,
            )
    else:
        # User is not logged in, redirect to the login page
        return redirect(url_for("login_page"))


# Add to wishlist
@app.route("/add_watchlist", methods=["POST"])
def add_watchlist():
    if request.method == "POST":
        if "username" in session:
            data_received = request.get_json()
            cur = mysql.connection.cursor()

            username = session["username"]
            query = "SELECT * FROM store WHERE storename = %s;"
            cur.execute(query, (username,))
            store_data = cur.fetchone()
            cur.close()

            store_id = store_data[0]

            try:
                cur = mysql.connection.cursor()

                insert_query = "INSERT INTO watchlist (storeId, watched_id, watched_type) VALUES (%s, %s, %s)"
                print(data_received["watched_id"])
                print(store_id)
                print(data_received["watched_type"])
                cur.execute(
                    insert_query,
                    (
                        store_id,
                        data_received["watched_id"],
                        data_received["watched_type"],
                    ),
                )

                mysql.connection.commit()
                cur.close()

                return jsonify(
                    {"message": "Data inserted into the database successfully"}
                )
            except Exception as e:
                # Handle the database insertion error
                mysql.connection.rollback()
                return jsonify({"error": str(e)})

# Remove from wishlist
@app.route("/remove_watchlist", methods=["POST"])
def remove_watchlist():
    if request.method == "POST":
        if "username" in session:
            data_received = request.get_json()
            cur = mysql.connection.cursor()

            username = session["username"]
            query = "SELECT * FROM store WHERE storename = %s;"
            cur.execute(query, (username,))
            store_data = cur.fetchone()
            cur.close()

            store_id = store_data[0]

            try:
                cur = mysql.connection.cursor()

                delete_query = "DELETE FROM watchlist WHERE storeId=%s AND watched_id=%s AND watched_type=%s"
                print(data_received["watched_id"])
                print(store_id)
                print(data_received["watched_type"])
                cur.execute(
                    delete_query,
                    (
                        store_id,
                        data_received["watched_id"],
                        data_received["watched_type"],
                    ),
                )

                mysql.connection.commit()
                cur.close()

                return jsonify(
                    {"message": "Data deleted from the database successfully"}
                )
            except Exception as e:
                # Handle the database deletion error
                mysql.connection.rollback()
                return jsonify({"error": str(e)})


if __name__ == "__main__":
    app.run(debug=True)
