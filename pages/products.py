import traceback
from flask import Flask, Blueprint, render_template, request, redirect, url_for, session
from model import *
from utils import *

from decimal import Decimal
from langchain.agents import create_csv_agent

from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.agents.agent_types import AgentType
from dotenv import load_dotenv

from langchain import OpenAI, SQLDatabase, SQLDatabaseChain

load_dotenv()

products_blueprint = Blueprint("products", __name__)


# Products Page
@products_blueprint.route("/products", methods=["GET"])
def products_page():
    if "username" in session:
        username = session["username"]

        cur = mysql.connection.cursor()
        # original query
        # query = "SELECT p.productid, p.ProductName, p.Productdesc, p.sellingprice, p.discountedprice, p.category, p.quantitysold, p.productlikes, p.productratings, p.productratingsamt, p.shippingtype, p.shipfrom FROM product p INNER JOIN store s ON p.storeid = s.storeid WHERE s.storename = %s;"

        # v1 query
        query = "SELECT p.productid, p.ProductName, p.Productdesc, p.sellingprice, p.discountedprice, p.category, p.quantitysold, p.productlikes, p.productratings, p.productratingsamt, p.shippingtype, p.shipfrom, w.watchlistId FROM product p INNER JOIN store s ON p.storeid = s.storeid LEFT JOIN watchlist w ON p.productid = w.watched_id WHERE s.storename = %s;"

        # v2 query
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

        # old
        # stripped_data = [[str(item).strip() for item in row]
        #                 for row in fetchdata]

        # new
        stripped_data = [
            [str(item).strip() if item is not None else None for item in row]
            for row in fetchdata
        ]

        cur.close()
        return render_template(
            "products/products.html", data=stripped_data, username=username
        )
    else:
        return "User not logged in"


@products_blueprint.route("/editProduct/<int:product_id>", methods=["GET"])
def view_store(product_id):
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT p.productid,p.ProductName,p.Productdesc,p.sellingprice,p.discountedprice,p.category,p.quantitysold,p.productlikes,p.productratings,p.productratingsamt,p.shippingtype,p.shipfrom FROM product p INNER JOIN store s ON p.storeid = s.storeid WHERE p.productid = %s;",
        (product_id,),
    )
    fetchdata = cur.fetchall()

    cur.close()
    return render_template("products/editProduct.html", data=fetchdata)


@products_blueprint.route("/optimizeProduct/<int:product_id>", methods=["GET"])
def optimize(product_id):
    # Get a cursor object to execute SQL queries
    cur = mysql.connection.cursor()

    # Retrieve product data from the 'product' table and store it in 'fetchdata'
    cur.execute(
        "SELECT p.productid,p.ProductName,p.Productdesc,p.sellingprice,p.discountedprice,p.category,p.quantitysold,p.productlikes,p.productratings,p.productratingsamt,p.shippingtype,p.shipfrom FROM product p INNER JOIN store s ON p.storeid = s.storeid WHERE p.productid = %s;",
        (product_id,),
    )
    fetchdata = cur.fetchall()

    # Retrieve the category data of the product
    cur.execute(
        "SELECT p.category FROM product p INNER JOIN store s ON p.storeid = s.storeid WHERE p.productid = %s;",
        (product_id,),
    )
    category_data = cur.fetchall()

    # Split the categories and remove the first 3 values to get 'stripped_categories'
    categories = category_data[0][0].split(";")
    stripped_categories = [category.strip() for category in categories][3:]

    # Retrieve pricing data for products in the same category and with ratings between 1 and 5
    if stripped_categories:
        cur.execute(
            """
            SELECT p.sellingprice, p.discountedprice, p.productid
            FROM product p
            INNER JOIN (
                SELECT productid
                FROM product
                WHERE category LIKE %s
                AND productratings BETWEEN 1 AND 5
                ORDER BY productratings DESC
                LIMIT 10
            ) AS subquery ON p.productid = subquery.productid
            WHERE p.category LIKE %s;
            """,
            ["%" + stripped_categories[0] + "%", "%" + stripped_categories[0] + "%"],
        )

    pricing = cur.fetchall()
    # Retrieve the avg price, max price, min price for products in the same category and with ratings between 1 and 5
    cur.execute(
        """
        SELECT AVG(p.sellingprice) as avg_selling_price,
            AVG(p.discountedprice) as avg_discounted_price,
            MAX(p.sellingprice) as max_selling_price,
            MIN(p.discountedprice) as min_discounted_price
        FROM product p
        INNER JOIN (
            SELECT productid
            FROM product
            WHERE category LIKE %s
            AND productratings BETWEEN 1 AND 5
            ORDER BY productratings DESC
            LIMIT 10
        ) AS subquery ON p.productid = subquery.productid
        WHERE p.category LIKE %s;
    """,
        ["%" + stripped_categories[0] + "%", "%" + stripped_categories[0] + "%"],
    )
    avgprice = cur.fetchall()

    # Calculate the average rating for each stripped category and get all ratings
    if stripped_categories:
        average_ratings = []
        all_ratings = []
        for category in stripped_categories:
            cur.execute(
                """
                SELECT p.productratings
                FROM product p
                INNER JOIN store s ON p.storeid = s.storeid
                WHERE p.category LIKE %s
                AND p.productratings BETWEEN 1 AND 5
                ORDER BY p.productratings DESC
                """,
                ["%" + category + "%"],
            )
            ratings = cur.fetchall()
            all_ratings.extend([rating[0] for rating in ratings])
            average_rating = (
                sum([rating[0] for rating in ratings]) / len(ratings)
                if len(ratings) > 0
                else 0
            )
            average_ratings.append(average_rating)

    # Retrieve top-rated products and their product names in the same category and with ratings between 1 and 5
    cur.execute(
        """
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
        WHERE p.category LIKE %s;
        """,
        ["%" + stripped_categories[0] + "%", "%" + stripped_categories[0] + "%"],
    )
    top_rated_products = cur.fetchall()

    cur.close()

    # Tokenize product names and create a list of product keywords
    product_keywords = []
    for product in top_rated_products:
        product_name = product[0]
        tokens = word_tokenize(product_name)  # Tokenization
        product_keywords.append(tokens)

    # Flatten the list of product keywords
    flattened_keywords = [
        keyword for sublist in product_keywords for keyword in sublist
    ]

    # Count the frequency of each keyword
    keyword_counts = Counter(flattened_keywords)

    # Set the frequency threshold for common keywords
    frequency_threshold = 2

    # Filter out keywords that don't meet the frequency threshold and exclude symbols/numbers
    filtered_common_keywords = [
        (keyword, count)
        for keyword, count in keyword_counts.items()
        if count >= frequency_threshold and re.match(r"^[a-zA-Z]+$", keyword)
    ]

    # Render the 'optimizeProduct.html' template with the retrieved data and calculated values
    return render_template(
        "products/optimizeProduct.html",
        data=fetchdata,
        price=pricing,
        avgprice=avgprice,
        keywords=filtered_common_keywords,
        ratingData=all_ratings,
        avgrating=round(average_rating, 2),
    )


@products_blueprint.route("/delete_product", methods=["POST"])
def delete_product():
    product_id = request.form.get("id")
    print(product_id)
    # Connect to MySQL
    conn = mysql.connection
    cursor = conn.cursor()

    try:
        # Execute the delete query
        query = "DELETE FROM product WHERE productid = %s"
        cursor.execute(query, (product_id,))
        conn.commit()
        return redirect("/success")
    except Exception as error:
        # Handle any errors that occur during the deletion
        print(f"Error deleting product: {error}")
        return redirect("/404")

    finally:
        # Close the cursor
        cursor.close()


@products_blueprint.route("/addProduct", methods=["GET"])
def add_product():
    if "username" in session:
        username = session["username"]

        cur = mysql.connection.cursor()

        query = "SELECT storeId from store WHERE storename = %s;"
        category_query = "select distinct category from product;"
        shipfrom_query = "select distinct shipFrom from product;"

        cur.execute(query, (username,))
        fetchdata = cur.fetchall()

        cur.execute(category_query)
        category_data = cur.fetchall()
        # Remove parentheses and commas from category values
        category = [re.sub(r"[\(\),]", "", item[0]) for item in category_data]

        cur.execute(shipfrom_query)
        shipfrom_data = cur.fetchall()
        # Remove parentheses and commas from shipfrom values
        shipfrom = [re.sub(r"[\(\),]", "", item[0]) for item in shipfrom_data]

        return render_template(
            "products/addProduct.html",
            data=fetchdata,
            category=category,
            shipfrom=shipfrom,
        )


@products_blueprint.route("/addProductDB", methods=["POST"])
def add_productDB():
    # Extract data from the form
    product_name = request.form["ProductName"]
    product_description = request.form["ProductDescription"]
    product_categories = request.form["ProductCategories"]
    selling_price = request.form["sellingPrice"]
    storeID = request.form["id"]
    discount_percentage = request.form["discountPercentage"]
    discounted_price = (float(selling_price) * (100 - float(discount_percentage))) / 100
    quantity = request.form["Quantity"]
    free_shipping = request.form.get(
        "freeShipping"
    )  # It will be 'Free shipping' if checked or None if not checked
    shipFrom = request.form["shipFrom"]
    # Extract hidden fields
    product_slug = request.form["productSlug"]
    product_likes = request.form["productLikes"]
    product_rating = request.form["productrating"]
    product_ratings_amt = request.form["productratingsamt"]

    # Create a new Product object with the extracted data
    product = {
        "ProductName": product_name,
        "Productdesc": product_description,
        "sellingprice": selling_price,
        "discountedprice": discounted_price,
        "category": product_categories,
        "quantitysold": quantity,
        "productlikes": product_likes,
        "productratings": product_rating,
        "productratingsamt": product_ratings_amt,
        "shippingtype": "Free shipping" if free_shipping else "",
        "shipfrom": shipFrom,
        "productSlug": product_slug,
        "StoreId": storeID,
    }

    # Execute the SQL query to insert the new product into the database
    cur = mysql.connection.cursor()
    cur.execute(
        """
        INSERT INTO product (
            ProductName, Productdesc, sellingprice, discountedprice, category, quantitysold, 
            productlikes, productratings, productratingsamt, shippingtype, shipfrom, 
            productSlug, storeid
        )
        VALUES (
            %(ProductName)s, %(Productdesc)s, %(sellingprice)s, %(discountedprice)s, %(category)s, 
            %(quantitysold)s, %(productlikes)s, %(productratings)s, %(productratingsamt)s, 
            %(shippingtype)s, %(shipfrom)s, %(productSlug)s, %(StoreId)s
        )
    """,
        product,
    )

    # Commit the changes to the database
    mysql.connection.commit()

    # Close the cursor
    cur.close()

    # Redirect the user to a success page or back to the add product page
    # You can customize this URL to match your application's structure
    return redirect(
        url_for("success")
    )  # Replace 'products.add_product_page' with the actual URL of the add product page


@products_blueprint.route("/generate_listing", methods=["POST"])
def generate_listing():
    db = SQLDatabase.from_uri("mysql+pymysql://root:root@localhost/dbms")
    llm = OpenAI(
        openai_api_key="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",
        temperature=0,
        verbose=True,
    )
    # Set up your OpenAI API credentials
    db_chain = SQLDatabaseChain.from_llm(llm, db, verbose=True)
    product_categories = request.form["ProductCategories"]
    product = request.form["aiInput"]
    select_table = "this query you only need to understand product data"
    bot = "you are a product name generator bot, given the data, desciption of a product and category of product"
    data = "the data is data of current listed products.it has total 14 columns but you only need productName(name of product),productDesc(product description),selling price(selling price of product),discounted price (price of product after discount) , category( category of product concatenated based on their sub category) , products sold( number of products sold), productslikes (number of users that like this product), product rating (overall rating of a product by past buyers max is 5/5) and productRatingsAmt( which is the number of users that rate this producct)"
    analysis = "what constitutes a good product is one that has a high rating,high quanitity sold and high product ratings amt"
    user_input = (
        "based on the",
        product,
        "in",
        product_categories,
        " generate a good product name so that",
        product,
        " will be a good product.give me 3 suggestions of names and a short write up on keywords i should include in my product name also give me a suggested description",
    )
    designed_utput = "you should reply should be strictly this format.Based on the product name you provided here are the 3 names i suggest: .have a line break then new paragraph, these are the keywords you should include: have a line break next paragraph, these is a suggested decription. this is how you should structure your answer to reply"
    output = select_table, bot, data, analysis, user_input, designed_utput
    ai_output = db_chain.run(output)
    print("output of agent:", ai_output)
    return ai_output


@products_blueprint.route("/update_product", methods=["POST"])
def update_product():
    # Retrieve the form data
    id = request.form["id"]
    product_name = request.form["ProductName"]
    product_description = request.form["ProductDescription"]
    selling_price = decimal.Decimal(request.form["sellingPrice"])

    discountPercentage = decimal.Decimal(request.form["discountPercentage"])
    print(discountPercentage)
    discounted_price = (selling_price * (100 - discountPercentage)) / 100
    quantity = request.form["Quantity"]
    free_shipping = request.form.get("freeShipping")  # Checkbox value

    # Perform the update operation using the retrieved data and the ID
    cur = mysql.connection.cursor()
    sql = "UPDATE product SET productName = %s, productDesc = %s, sellingprice = %s, discountedprice = %s, quantitysold = %s, shippingtype = %s WHERE productId = %s"
    params = (
        product_name,
        product_description,
        selling_price,
        discounted_price,
        quantity,
        free_shipping,
        id,
    )

    print("SQL Statement:", sql)
    print("Parameters:", params)

    cur.execute(sql, params)

    print()
    mysql.connection.commit()
    cur.close()

    # Redirect to a success page or perform any other necessary action
    return redirect("/success")
