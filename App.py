from collections import Counter
import decimal
from itertools import count

from flask.json import jsonify
from helpers.database import *
import nltk
from nltk.tokenize import word_tokenize
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
from model import *
import re
from flask_mail import Mail, Message




app = Flask(__name__)
app.secret_key = "ITSASECRET"

# Configure MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
#app.config['MYSQL_PASSWORD'] = 'password' // for nicolas :(
app.config['MYSQL_DB'] = 'dbms'

# Create MySQL instance
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'tay.jiale@gmail.com'
app.config['MAIL_PASSWORD'] = 'tfclioagsaftodjo'
mail = Mail(app)
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

        if fetchdata:
            first_tuple = fetchdata[0]
            store_id = first_tuple[0]

        query_retrieve_watch_store =  """
            SELECT s.storeId, s.storeName, s.storejoineddate, s.platformtype, w.watchlistId FROM Store s 
            INNER JOIN watchlist w 
            ON s.storeId = w.watched_id
            WHERE w.storeId = %s
        """
        cur.execute(query_retrieve_watch_store, (store_id,))
        watch_store = cur.fetchall()
        
        query_retrieve_watch_product =  """
            SELECT p.productid, p.ProductName, p.Productdesc, p.sellingprice, p.discountedprice, p.category, p.quantitysold, p.productlikes, p.productratings, p.productratingsamt, p.shippingtype, p.shipfrom, w.watchlistId
            FROM product p
            INNER JOIN watchlist w 
            ON p.productid = w.watched_id
            WHERE w.storeId = %s AND w.watched_type ='product'
        """
        cur.execute(query_retrieve_watch_product, (store_id,))
        watch_product = cur.fetchall()
        count = 0
        for row in watch_product:
            count += 1
            print(count)
        cur.close()

        return render_template('index.html', username=username, data=fetchdata, performance=int(fetchdata[0][8] * 100), difference=rdiff, watch_store=watch_store, watch_product=watch_product)
    else:
        return render_template('login.html')


@app.route('/revenue', methods=["GET"])
def revenue():
    if 'username' in session:
        username = session['username']

        # Aggregate pipeline to calculate revenue
        revenue_pipeline = [
            {
                '$lookup': {
                    'from': 'store',
                    'localField': 'StoreID',
                    'foreignField': 'StoreID',
                    'as': 'store'
                }
            },
            {
                '$match': {
                    'store.storeName': username
                }
            },
            {
                '$project': {
                    '_id': 0,
                    'QuantitySold': 1,
                    'DiscountedPrice': 1,
                    'productName': 1,
                    'revenue': {'$multiply': ['$QuantitySold', '$DiscountedPrice']},
                    'StoreID': 1,
                }
            }
        ]

        # Aggregate pipeline to calculate total quantity sold
    quantity_sold_pipeline = [
        {
            '$lookup': {
                'from': 'store',
                'localField': 'StoreID',
                'foreignField': 'StoreID',
                'as': 'store'
            }
        },


        {

            '$match': {
                'store.storeName': username
            }
        },
        {
            '$sort': {
                'QuantitySold': -1
            }
        },
        {
            '$limit': 10
        },
        {
            '$project': {
                '_id': 0,
                'productName': 1,
                'totalQuantitySold': '$QuantitySold'
            }
        }
    ]

    price_range_pipeline = [
        {
            '$lookup': {
                'from': 'store',
                'localField': 'StoreID',
                'foreignField': 'StoreID',
                'as': 'store'
            }
        },
        {
            '$match': {
                'store.storeName': username
            }
        },
        {
            '$project': {
                'productName': 1,
                'revenue': {'$multiply': ['$QuantitySold', '$DiscountedPrice']},
                'priceRange': {
                    '$switch': {
                        'branches': [
                            {'case': {'$and': [{'$gte': ['$DiscountedPrice', 0]}, {
                                '$lt': ['$DiscountedPrice', 2]}]}, 'then': 'Low'},
                            {'case': {'$and': [{'$gte': ['$DiscountedPrice', 3]}, {
                                '$lt': ['$DiscountedPrice', 5]}]}, 'then': 'Medium'},
                            {'case': {'$and': [{'$gte': ['$DiscountedPrice', 5]}, {
                                '$lt': ['$DiscountedPrice', 7]}]}, 'then': 'High'}
                        ],
                        'default': 'Other'
                    }
                }
            }
        },
        {
            '$group': {
                '_id': {
                    'priceRange': '$priceRange',
                    'productName': '$productName'
                },
                'revenue': {'$sum': '$revenue'}
            }
        },
        {
            '$group': {
                '_id': '$_id.priceRange',
                'products': {'$push': {'productName': '$_id.productName', 'revenue': '$revenue'}},
                'totalRevenue': {'$sum': '$revenue'}
            }
        },
        {
            '$sort': {
                '_id': 1
            }
        }
    ]

    forecast_pipeline = [
        {
            '$lookup': {
                'from': 'products_temp',
                'localField': 'ProductID',
                'foreignField': 'productId',
                'as': 'product'
            }
        },
        {
            '$lookup': {
                'from': 'store',
                'localField': 'StoreID',
                'foreignField': 'StoreID',
                'as': 'store'
            }
        },
           {
        '$match': {
            'store.storeName': username        }
        
    },
        {
            '$unwind': '$product'
        },
        {
            '$group': {
                '_id': {
                    'year': {'$year': {'$dateFromString': {'dateString': '$Date', 'format': '%d/%m/%Y'}}},
                    'month': {'$month': {'$dateFromString': {'dateString': '$Date', 'format': '%d/%m/%Y'}}},
                    'productName': '$product.productName'
                },
                'quantitySold': {'$sum': '$Quantity'},
                'productID': {'$first': '$ProductID'}
            }
        },
        {
            '$project': {
                '_id': 0,
                'year': '$_id.year',
                'month': '$_id.month',
                'productName': '$_id.productName',
                'quantitySold': 1,
                'productID': 1,
                'StoreID': 1,
                'store.storeName': '$store.storeName'
            }
        },
        {
            '$sort': {
                'year': 1,
                'month': 1
            }
        }
    ]

    revenue_data = list(db.products.aggregate(revenue_pipeline))
    quantity_sold_data = list(db.products.aggregate(quantity_sold_pipeline))
    price_range_data = list(db.products.aggregate(price_range_pipeline))
    print('Username:', username)
    forecast_data = list(db.order.aggregate(forecast_pipeline))

    # for item in price_range_data:
    #     print('Price Range:', item['_id'])
    #     print('Total Revenue:', item['totalRevenue'])
    #     print('Products:', item['products'])
    #     # print('Output:', item['output'])
    #     print('---')

    # for doc in revenue_data:
    #     print('Quantity Sold:', doc['QuantitySold'])
    #     print('Discounted Price:', doc['DiscountedPrice'])
    #     print('Revenue:', doc['revenue'])
    #     # print('Total Quantity:', doc['totalQuantitySold'])
    #     print(doc['productName'])

    for doc in forecast_data:
     
        print(doc)

    return render_template("revenue.html", revenue_data=revenue_data, username=username,  quantity_sold_data=quantity_sold_data, price_range_data=price_range_data, forecast_data=forecast_data)


# Tables Page
@app.route('/tables', methods=["GET"])
def tables():
    if 'username' in session:
        username = session['username']

        cur = mysql.connection.cursor()
        #original query
        # query = "SELECT p.productid, p.ProductName, p.Productdesc, p.sellingprice, p.discountedprice, p.category, p.quantitysold, p.productlikes, p.productratings, p.productratingsamt, p.shippingtype, p.shipfrom FROM product p INNER JOIN store s ON p.storeid = s.storeid WHERE s.storename = %s;"
        
        # v1 query
        query = "SELECT p.productid, p.ProductName, p.Productdesc, p.sellingprice, p.discountedprice, p.category, p.quantitysold, p.productlikes, p.productratings, p.productratingsamt, p.shippingtype, p.shipfrom, w.watchlistId FROM product p INNER JOIN store s ON p.storeid = s.storeid LEFT JOIN watchlist w ON p.productid = w.watched_id WHERE s.storename = %s;"
        
        #v2 query
        # query = """
        #     SELECT p.productid, p.ProductName, p.Productdesc, p.sellingprice, p.discountedprice, p.category,
        #            p.quantitysold, p.productlikes, p.productratings, p.productratingsamt,
        #            p.shippingtype, p.shipfrom
        #     FROM product p
        #     INNER JOIN store s ON p.storeid = s.storeid
        #     LEFT JOIN watchlist w ON p.productid = w.watched_id
        #     WHERE s.storename = %s;
        # """
        
        cur.execute(query, (username,))
        fetchdata = cur.fetchall()
        
        #old
        # stripped_data = [[str(item).strip() for item in row]
        #                 for row in fetchdata]

        #new
        stripped_data = [[str(item).strip() if item is not None else None for item in row]
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
        #query = "SELECT storeID,storename,storejoineddate,platformtype FROM store;"
        query = "SELECT s.storeID, s.storename, s.storejoineddate, s.platformtype, w.watchlistId FROM Store s LEFT JOIN watchlist w ON s.storeID = w.watched_id"
        
        cur.execute(query)
        fetchdata = cur.fetchall()
        # stripped_data = [[str(item).strip() for item in row]
        #                  for row in fetchdata]
        stripped_data = [[str(item).strip() if item is not None else None for item in row]
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

@app.route('/getCatP')
def getcat():
    cur = mysql.connection.cursor()
    cur.execute("SELECT category FROM product p INNER JOIN store s ON p.storeId = s.storeId WHERE s.storeName = %s", (session['username'],))
    fetchdata = cur.fetchall()
    cur.close()

    category_dict = {}

    for row in fetchdata:
        category_string = row[0]
        category_values = category_string.split(';')

        main_category = category_values[2]
        subcategories = category_values[3:]

        main_category_dict = category_dict.setdefault(main_category, set())

        for subcategory in subcategories:
            if ':' in subcategory:
                break  # Stop processing subcategories when a tuple is encountered

            main_category_dict.add(subcategory)

    main_categories = list(category_dict.keys())  # Get the main categories
    sub_categories = {main_category: list(subs) for main_category, subs in category_dict.items()}  # Convert subcategories to dictionary format

    return render_template('CatProducts.html', main_categories=main_categories, sub_categories=sub_categories)


from decimal import Decimal
import json

@app.route('/get-product-cat', methods=["GET"])
def get_product_cat():
    main_category = request.args.get('main_category')
    sub_categories = request.args.getlist('sub_categories')

    cur = mysql.connection.cursor()

    # Construct the SQL query based on the selected main category and subcategories
    query = """
        SELECT *
        FROM product
        WHERE category LIKE %s
    """
    params = [f'%{main_category}%']

    if sub_categories:
        query += "AND ("
        for i in range(len(sub_categories)):
            query += "category LIKE %s"
            params.append(f'%{sub_categories[i]}%')
            if i < len(sub_categories) - 1:
                query += " AND "
        query += ")"

    cur.execute(query, params)
    print(query, params)

    fetchdata = cur.fetchall()

    cur.close()

    # Convert Decimal objects to string representations
    serialized_data = []
    for row in fetchdata:
        serialized_row = [str(item) if isinstance(item, Decimal) else item for item in row]
        serialized_data.append(serialized_row)

    # Return JSON response
    return json.dumps(serialized_data)






    # Redirect to a success page or perform any other necessary action
    


@app.route('/generateotp', methods=['GET','POST'])
def generateotp():
        if request.method == 'POST':
            otp_username = request.form.get('username')
            print(otp_username)
            check = db.user.find_one({"username":  otp_username})

                # Generate a random 6-digit password
            otp = str(random.randint(100000, 999999))

            # Send the 6-digit password to the user's email
            msg = Message("2FA Verification Code", sender="your-email@example.com", recipients=[check["email"]])
            msg.body = f"Your verification code is: {otp}"
            mail.send(msg)
            # Store the generated OTP in the session
            session["otp"] = otp
           
            return otp
           
        else:
            return render_template('login.html') # Render the login form
        
@app.route('/validateotp', methods=['POST'])
def validate_otp():
    user_entered_otp = request.form.get('otp')  # Get the OTP submitted by the user

    if user_entered_otp == session['otp']:
        return jsonify({'result': 'success'})  # OTP is correct
    else:
        return jsonify({'result': 'error'})  # OTP is incorrect

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
            return render_template('login.html')
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

# Add to wishlist
@app.route('/add_watchlist', methods=['POST'])
def add_watchlist():
    if request.method == 'POST':
        if 'username' in session:
            data_received = request.get_json()
            cur = mysql.connection.cursor()

            username = session['username']
            query = "SELECT * FROM store WHERE storename = %s;"
            cur.execute(query, (username,))
            store_data = cur.fetchone()
            cur.close()
            
            store_id = store_data[0]

            try:
                cur = mysql.connection.cursor()

                insert_query = "INSERT INTO watchlist (storeId, watched_id, watched_type) VALUES (%s, %s, %s)"
                print(data_received['watched_id'])
                print(store_id)
                print(data_received['watched_type'])
                cur.execute(insert_query, (store_id,data_received['watched_id'],data_received['watched_type']))

                mysql.connection.commit()
                cur.close()
                
                return jsonify({"message": "Data inserted into the database successfully"})
            except Exception as e:
                # Handle the database insertion error
                mysql.connection.rollback()
                return jsonify({"error": str(e)})
            
@app.route('/remove_watchlist', methods=['POST'])
def remove_watchlist():
    if request.method == 'POST':
        if 'username' in session:
            data_received = request.get_json()
            cur = mysql.connection.cursor()

            username = session['username']
            query = "SELECT * FROM store WHERE storename = %s;"
            cur.execute(query, (username,))
            store_data = cur.fetchone()
            cur.close()
            
            store_id = store_data[0]

            try:
                cur = mysql.connection.cursor()

                delete_query = "DELETE FROM watchlist WHERE storeId=%s AND watched_id=%s AND watched_type=%s"
                print(data_received['watched_id'])
                print(store_id)
                print(data_received['watched_type'])
                cur.execute(delete_query, (store_id,data_received['watched_id'],data_received['watched_type']))

                mysql.connection.commit()
                cur.close()
                
                return jsonify({"message": "Data deleted from the database successfully"})
            except Exception as e:
                # Handle the database deletion error
                mysql.connection.rollback()
                return jsonify({"error": str(e)})
            
if __name__ == "__main__":
    app.run(debug=True)
