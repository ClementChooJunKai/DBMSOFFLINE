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
    storeDataquery = "SELECT * FROM store WHERE storename = %s;"
    productcount_query = "SELECT COUNT(*) FROM product p INNER JOIN store s ON p.storeid = s.storeid WHERE storename = %s;"
    top_earnings_query = """
                    SELECT s.storename, SUM(p.quantitysold * p.discountedprice) AS total_earnings
                    FROM product AS p
                    INNER JOIN store AS s ON p.storeid = s.storeid
                    GROUP BY s.storename
                    ORDER BY total_earnings DESC
                    LIMIT %s;
                """
    bottom_earnings_query = """
                    SELECT s.storename, SUM(p.quantitysold * p.discountedprice) AS total_earnings
                    FROM product AS p
                    INNER JOIN store AS s ON p.storeid = s.storeid
                    GROUP BY s.storename
                    ORDER BY total_earnings ASC
                    LIMIT %s;
                """
    earnings_query = """
            SELECT SUM(p.quantitysold * p.discountedprice) AS total_earnings
            FROM product AS p
            INNER JOIN store AS s ON p.storeid = s.storeid
            WHERE s.storename = %s;
        """
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
    query_retrieve_watch_store = """
            SELECT s.storeId, s.storeName, s.storejoineddate, s.platformtype, w.watchlistId FROM Store s 
            INNER JOIN watchlist w 
            ON s.storeId = w.watched_id
            WHERE w.storeId = %s
        """
    query_retrieve_watch_product = """
            SELECT p.productid, p.ProductName, p.Productdesc, p.sellingprice, p.discountedprice, p.category, p.quantitysold, p.productlikes, p.productratings, p.productratingsamt, p.shippingtype, p.shipfrom, w.watchlistId
            FROM product p
            INNER JOIN watchlist w 
            ON p.productid = w.watched_id
            WHERE w.storeId = %s AND w.watched_type ='product'
        """
    productcount_query = "SELECT COUNT(*) FROM product p INNER JOIN store s ON p.storeid = s.storeid WHERE storename = %s;"
    if request.method == "POST":
        if "username" in session:
            shop_count = 2
            username = session["username"]
            cur = mysql.connection.cursor()
            cur.execute(storeDataquery, (username,))
            fetchdata = cur.fetchall()

            cur.execute(productcount_query, (username,))
            productcount_data = cur.fetchone()
            productcount = productcount_data[0]

            shop_selection = request.form.get("shopSelection")
            shop_count = int(request.form.get("shopCount"))

            earning = []  # Initialize with an empty list
            bottom_earnings_data = []  # Initialize with an empty list

            if shop_selection == "top":
                cur.execute(top_earnings_query, (shop_count,))
                earnings_data = cur.fetchall()
                earning = [
                    (storename, float(total_earnings))
                    for storename, total_earnings in earnings_data
                ]
            elif shop_selection == "bottom":
                cur.execute(bottom_earnings_query, (shop_count,))
                bottom_earnings_data = cur.fetchall()
            else:
                earning = []

            cur.execute(earnings_query, (username,))
            earnings_data = cur.fetchone()
            total_earnings = earnings_data[0] if earnings_data[0] is not None else 0

            cur.execute(rating_difference_query, (username,))
            rating_difference_data = cur.fetchone()
            rating_difference = (
                rating_difference_data[1] if rating_difference_data is not None else 0
            )

            if rating_difference >= 0:
                rdiff = "You are above average by : " + str(round(rating_difference, 2))
            else:
                rdiff = "You are below average by : " + str(
                    round(rating_difference, 2)
                ).strip("-")

            if fetchdata:
                first_tuple = fetchdata[0]
                store_id = first_tuple[0]

            cur.execute(query_retrieve_watch_store, (store_id,))
            watch_store = cur.fetchall()

            cur.execute(query_retrieve_watch_product, (store_id,))
            watch_product = cur.fetchall()
            count = 0
            for row in watch_product:
                count += 1
                print(count)
            cur.close()

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

    # The remaining code for the 'GET' request remains the same as before
    if "username" in session:
        username = session["username"]
        cur = mysql.connection.cursor()
        cur.execute(
            storeDataquery, (username,)
        )  # Getting all the data from the store table
        fetchdata = cur.fetchall()

        cur.execute(productcount_query, (username,))
        productcount_data = cur.fetchone()  # Use fetchone() instead of fetchall()
        productcount = productcount_data[0]

        cur.execute(earnings_query, (username,))
        earnings_data = cur.fetchone()

        total_earnings = earnings_data[0] if earnings_data[0] is not None else 0

        cur.execute(rating_difference_query, (username,))#except the rating difference
        rating_difference_data = cur.fetchone()
        rating_difference = (
            rating_difference_data[1] if rating_difference_data is not None else 0
        )

        if rating_difference >= 0:
            rdiff = "You are above average by : " + str(round(rating_difference, 2))
        else:
            rdiff = "You are below average by : " + str(
                round(rating_difference, 2)
            ).strip("-")

        if fetchdata:
            first_tuple = fetchdata[0]
            store_id = first_tuple[0]

        cur.execute(query_retrieve_watch_store, (store_id,))
        watch_store = cur.fetchall()

        cur.execute(query_retrieve_watch_product, (store_id,))
        watch_product = cur.fetchall()
        count = 0
        for row in watch_product:
            count += 1
            print(count)
        cur.close()

        return render_template("index.html",username=username,data=fetchdata,productcount=productcount,performance=int(fetchdata[0][8] * 100),difference=rdiff,watch_store=watch_store,watch_product=watch_product,)
    else:
        return render_template("login.html")


@app.route("/generateotp", methods=["GET", "POST"])
def generateotp():
    if request.method == "POST":
        otp_username = request.form.get("username")
        print(otp_username)
        check = db.user.find_one({"username": otp_username})

        # Generate a random 6-digit password
        otp = str(random.randint(100000, 999999))

        # Send the 6-digit password to the user's email
        msg = Message(
            "2FA Verification Code",
            sender="your-email@example.com",
            recipients=[check["email"]],
        )
        msg.body = f"Your verification code is: {otp}"
        mail.send(msg)
        # Store the generated OTP in the session
        session["otp"] = otp

        return otp

    else:
        return render_template("login.html")  # Render the login form


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


# Cards Page
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


# Charts Page


@app.route("/charts", methods=["GET"])
def charts():
    return render_template("charts.html")


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
