from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
from model import *
from utils import *  
from pages.revenue import revenue_blueprint

app = Flask(__name__)
app = configure_app(app)
app.register_blueprint(revenue_blueprint)

# Create MySQL instance
mysql = MySQL(app)


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        if 'username' in session:
            shop_count = 2
            username = session['username']
            cur = mysql.connection.cursor()
            username = session['username']
            query = "SELECT * FROM store WHERE storename = %s;"
            cur.execute(query, (username,))

            fetchdata = cur.fetchall()
            # Retrieve the filter parameters from the request
            shop_selection = request.form.get('shopSelection')

            shop_count = int(request.form.get('shopCount'))

            # Construct and execute the SQL query based on the filter parameters
            if shop_selection == 'top':
                top_earnings_query = """
                    SELECT s.storename, SUM(p.quantitysold * p.discountedprice) AS total_earnings
                    FROM product AS p
                    INNER JOIN store AS s ON p.storeid = s.storeid
                    GROUP BY s.storename
                    ORDER BY total_earnings DESC
                    LIMIT %s;
                """
                cur.execute(top_earnings_query, (shop_count,))
                earnings_data = cur.fetchall()
                earning = [(storename, float(total_earnings))
                           for storename, total_earnings in earnings_data]
                # Process the filtered data as needed
                print(earning)
                cur.close()
                return render_template('index.html', username=username, data=fetchdata, performance=int(fetchdata[0][8] * 100), earning=earning)
            elif shop_selection == 'bottom':
                bottom_earnings_query = """
                    SELECT s.storename, SUM(p.quantitysold * p.discountedprice) AS total_earnings
                    FROM product AS p
                    INNER JOIN store AS s ON p.storeid = s.storeid
                    GROUP BY s.storename
                    ORDER BY total_earnings ASC
                    LIMIT %s;
                """
                cur.execute(bottom_earnings_query, (shop_count,))
                bottom_earnings_data = cur.fetchall()
                # Process the filtered data as needed
                print(bottom_earnings_data)

                cur.close()
                return render_template('index.html', username=username, data=fetchdata, performance=int(fetchdata[0][8] * 100), earning=bottom_earnings_data)

    # The remaining code for the 'GET' request remains the same as before
    if 'username' in session:
        username = session['username']
        cur = mysql.connection.cursor()
        query = "SELECT * FROM store WHERE storename = %s;"
        cur.execute(query, (username,))

        fetchdata = cur.fetchall()
        earnings_query = """
            SELECT SUM(p.quantitysold * p.discountedprice) AS total_earnings
            FROM product AS p
            INNER JOIN store AS s ON p.storeid = s.storeid
            WHERE s.storename = %s;
        """
        cur.execute(earnings_query, (username,))
        earnings_data = cur.fetchone()

        total_earnings = earnings_data[0] if earnings_data[0] is not None else 0

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
        cur.execute(rating_difference_query, (username,))
        rating_difference_data = cur.fetchone()
        rating_difference = rating_difference_data[1] if rating_difference_data is not None else 0
        print(rating_difference)

        if rating_difference >= 0:
            rdiff = "You are above average by : " + \
                str(round(rating_difference, 2))
        else:
            rdiff = "You are below average by : " + \
                str(round(rating_difference, 2)).strip("-")

        cur.close()
        return render_template('index.html', username=username, data=fetchdata, performance=int(fetchdata[0][8] * 100), difference=rdiff)
    else:
        return render_template('login.html')



# Tables Page
@app.route('/tables', methods=["GET"])
def tables():
    if 'username' in session:
        username = session['username']

        cur = mysql.connection.cursor()
        query = "SELECT p.productid, p.ProductName, p.Productdesc, p.sellingprice, p.discountedprice, p.category, p.quantitysold, p.productlikes, p.productratings, p.productratingsamt, p.shippingtype, p.shipfrom FROM product p INNER JOIN store s ON p.storeid = s.storeid WHERE s.storename = %s;"
        cur.execute(query, (username,))
        fetchdata = cur.fetchall()
        stripped_data = [[str(item).strip() for item in row]
                         for row in fetchdata]
        cur.close()
        return render_template("tables.html", data=stripped_data, username=username)
    else:
        return "User not logged in"


# Stores Page
@app.route('/Stores', methods=["GET"])
def stores():
    if 'username' in session:
        username = session['username']

        cur = mysql.connection.cursor()
        query = "SELECT storeID,storename,storejoineddate,platformtype FROM store;"
        cur.execute(query)
        fetchdata = cur.fetchall()
        stripped_data = [[str(item).strip() for item in row]
                         for row in fetchdata]
        cur.close()
        return render_template("store.html", data=stripped_data, username=username)
    else:
        return "User not logged in"


@app.route('/blank/<int:product_id>', methods=['GET'])
def view_store(product_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT p.productid,p.ProductName,p.Productdesc,p.sellingprice,p.discountedprice,p.category,p.quantitysold,p.productlikes,p.productratings,p.productratingsamt,p.shippingtype,p.shipfrom FROM product p INNER JOIN store s ON p.storeid = s.storeid WHERE p.productid = %s;", (product_id,))
    fetchdata = cur.fetchall()

    cur.close()
    return render_template("blank.html", data=fetchdata)


@app.route('/optimize/<int:product_id>', methods=['GET'])
def optimize(product_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT p.productid,p.ProductName,p.Productdesc,p.sellingprice,p.discountedprice,p.category,p.quantitysold,p.productlikes,p.productratings,p.productratingsamt,p.shippingtype,p.shipfrom FROM product p INNER JOIN store s ON p.storeid = s.storeid WHERE p.productid = %s;", (product_id,))
    fetchdata = cur.fetchall()
    cur.execute(
        "SELECT p.category FROM product p INNER JOIN store s ON p.storeid = s.storeid WHERE p.productid = %s;", (product_id,))
    category_data = cur.fetchall()

    categories = category_data[0][0].split(";")

# Skip the first value of stripped_categories
# Assume you have an array of stripped categories
    stripped_categories = [category.strip() for category in categories][3:]

    if stripped_categories:
        cur.execute("""
        SELECT p.sellingprice, p.discountedprice,p.productid
        FROM product p
        INNER JOIN (
            SELECT productid
            FROM product
            WHERE category LIKE %s
            AND productratings BETWEEN 1 AND 5
            ORDER BY productratings DESC
            LIMIT 10
        ) AS subquery ON p.productid = subquery.productid
        INNER JOIN store s ON p.storeid = s.storeid
        WHERE p.category LIKE %s;
    """, ['%' + stripped_categories[0] + '%', '%' + stripped_categories[0] + '%'])
    pricing = cur.fetchall()

    if stripped_categories:
        # Calculate the average rating for each stripped category
        average_ratings = []
        all_ratings = []
        for category in stripped_categories:
            cur.execute("""
                SELECT p.productratings
                FROM product p
                INNER JOIN store s ON p.storeid = s.storeid
                WHERE p.category LIKE %s
                AND p.productratings BETWEEN 1 AND 5
                ORDER BY p.productratings DESC
                
            """, ['%' + category + '%'])
            ratings = cur.fetchall()
            all_ratings.extend([rating[0] for rating in ratings])
            average_rating = sum([rating[0] for rating in ratings]) / \
                len(ratings) if len(ratings) > 0 else 0
            average_ratings.append(average_rating)

    # Fetch top-rated products and their product names
    cur.execute("""
        SELECT p.ProductName
        FROM product p
        INNER JOIN (
            SELECT productid
            FROM product
            WHERE category LIKE %s
            AND productratings BETWEEN 1 AND 5
            ORDER BY productratings DESC
            LIMIT 10
        ) AS subquery ON p.productid = subquery.productid
        INNER JOIN store s ON p.storeid = s.storeid
        WHERE p.category LIKE %s;
    """, ['%' + stripped_categories[0] + '%', '%' + stripped_categories[0] + '%'])
    top_rated_products = cur.fetchall()

    cur.close()
    product_keywords = []
    for product in top_rated_products:
        product_name = product[0]
        tokens = word_tokenize(product_name)  # Tokenization
        product_keywords.append(tokens)

    # Flatten the list of product keywords
    flattened_keywords = [
        keyword for sublist in product_keywords for keyword in sublist]

    # Count the frequency of each keyword
    keyword_counts = Counter(flattened_keywords)

    # Set the frequency threshold
    frequency_threshold = 2

    # Filter out keywords that don't meet the frequency threshold and exclude symbols/numbers
    filtered_common_keywords = [(keyword, count) for keyword, count in keyword_counts.items(
    ) if count >= frequency_threshold and re.match(r'^[a-zA-Z]+$', keyword)]

    return render_template("optimize.html", data=fetchdata, price=pricing, keywords=filtered_common_keywords, ratingData=all_ratings, avgrating=round(average_rating, 2))


@app.route('/compare/<int:store_id>', methods=['GET'])
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

    return render_template("compare.html", cstore=cstore, data=fetchdata, compscore=round(fetchdata[0][3], 3), storecomp=round(owndata[0][3], 3), storedata=owndata, selfdata=ownstore)


@app.route('/delete_product', methods=['POST'])
def delete_product():
    product_id = request.form.get('id')
    print(product_id)
    # Connect to MySQL
    conn = mysql.connection
    cursor = conn.cursor()

    try:
        # Execute the delete query
        query = "DELETE FROM product WHERE productid = %s"
        cursor.execute(query, (product_id,))
        conn.commit()
        return redirect('/success')
    except Exception as error:
        # Handle any errors that occur during the deletion
        print(f"Error deleting product: {error}")
        return redirect('/404')

    finally:
        # Close the cursor
        cursor.close()


@app.route('/update_product', methods=['POST'])
def update_product():
    # Retrieve the form data
    id = request.form['id']
    product_name = request.form['ProductName']
    product_description = request.form['ProductDescription']
    selling_price = decimal.Decimal(request.form['sellingPrice'])

    discountPercentage = decimal.Decimal(request.form['discountPercentage'])
    print(discountPercentage)
    discounted_price = (selling_price*(100-discountPercentage))/100
    quantity = request.form['Quantity']
    free_shipping = request.form.get('freeShipping')  # Checkbox value

    # Perform the update operation using the retrieved data and the ID
    cur = mysql.connection.cursor()
    sql = "UPDATE product SET productName = %s, productDesc = %s, sellingprice = %s, discountedprice = %s, quantitysold = %s, shippingtype = %s WHERE productId = %s"
    params = (product_name, product_description, selling_price,
              discounted_price, quantity, free_shipping, id)

    print("SQL Statement:", sql)
    print("Parameters:", params)

    cur.execute(sql, params)

    print()
    mysql.connection.commit()
    cur.close()

    # Redirect to a success page or perform any other necessary action
    return redirect('/success')


@app.route('/success')
def success():
    return render_template('success.html')


@app.route('/index')
def dash():
    return render_template('index.html')


@app.route('/', methods=["GET"])
def login_page():
    if "username" in session:
        return render_template('index.html')
    else:
        return render_template('login.html')

# Register new user


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    elif request.method == "POST":
        registerUser()
        return redirect(url_for("login"))

# Check if email already exists in the registration page


@app.route('/checkusername', methods=["POST"])
def check_username():
    return checkusername()

# Everything Login (Routes to render page, check if username exists, and also verify password through Jquery AJAX request)


@app.route('/login', methods=["GET"])
def login():
    if request.method == "GET":
        if "username" not in session:
            return render_template("login.html")
        else:
            return redirect(url_for("home"))

# Check if username exists


@app.route('/checkloginusername', methods=["POST"])
def check_login_username():
    return checkloginusername()

# Check if password is correct


@app.route('/checkloginpassword', methods=["POST"])
def check_login_password():
    return checkloginpassword()

# The admin logout


@app.route('/logout', methods=["GET"])
def logout():
    session.pop('username', None)  # remove user session
    return redirect(url_for("home"))  # redirect to home page with message

# Forgot Password


@app.route('/forgot-password', methods=["GET"])
def forgot_password():
    return render_template('forgot-password.html')

# 404 Page


@app.route('/404', methods=["GET"])
def error_page():
    return render_template("404.html")

# Blank Page


@app.route('/blank', methods=["GET"])
def blank():
    return render_template('blank.html')
# Blank Page


@app.route('/profile', methods=["GET"])
def settings():
    return render_template('profile.html')


@app.route('/buttons', methods=["GET"])
def buttons():
    return render_template("buttons.html")

# Cards Page


@app.route('/cards', methods=["GET"])
def cards():
    return render_template('cards.html')

# Charts Page


@app.route('/charts', methods=["GET"])
def charts():
    return render_template("charts.html")


# Utilities-animation
@app.route('/utilities-animation', methods=["GET"])
def utilities_animation():
    return render_template("utilities-animation.html")

# Utilities-border


@app.route('/utilities-border', methods=["GET"])
def utilities_border():
    return render_template("utilities-border.html")

# Utilities-color


@app.route('/utilities-color', methods=["GET"])
def utilities_color():
    return render_template("utilities-color.html")

# Utilities-other


@app.route('/utilities-other', methods=["GET"])
def utilities_other():
    return render_template("utilities-other.html")


if __name__ == "__main__":
    app.run(debug=True)
