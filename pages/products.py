
from flask import Flask, Blueprint, render_template, request, redirect, url_for, session
from model import *
from utils import *

from decimal import Decimal

products_blueprint = Blueprint('products', __name__)


# Products Page
@products_blueprint.route('/products', methods=["GET"])
def products_page():
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
        return render_template("products/products.html", data=stripped_data, username=username)
    else:
        return "User not logged in"
    
    


@products_blueprint.route('/editProduct/<int:product_id>', methods=['GET'])
def view_store(product_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT p.productid,p.ProductName,p.Productdesc,p.sellingprice,p.discountedprice,p.category,p.quantitysold,p.productlikes,p.productratings,p.productratingsamt,p.shippingtype,p.shipfrom FROM product p INNER JOIN store s ON p.storeid = s.storeid WHERE p.productid = %s;", (product_id,))
    fetchdata = cur.fetchall()

    cur.close()
    return render_template("products/editProduct.html", data=fetchdata)


@products_blueprint.route('/optimizeProduct/<int:product_id>', methods=['GET'])
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

    return render_template("products/optimizeProduct.html", data=fetchdata, price=pricing, keywords=filtered_common_keywords, ratingData=all_ratings, avgrating=round(average_rating, 2))


@products_blueprint.route('/delete_product', methods=['POST'])
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


@products_blueprint.route('/update_product', methods=['POST'])
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