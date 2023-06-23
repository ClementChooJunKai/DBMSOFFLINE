import decimal

from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
from model import *

app = Flask(__name__)
app.secret_key = "ITSASECRET"

# Configure MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'dbms'

# Create MySQL instance
mysql = MySQL(app)

@app.route('/', methods=["GET"])
def home():
    if "username" in session:
        return render_template('index.html')
    else:
        return render_template('login.html')

# # Tables Page
# @app.route('/tables', methods=["GET"])
# def tables():
#     cur = mysql.connection.cursor()
#     cur.execute("SELECT p.productid,p.ProductName,p.Productdesc,p.sellingprice,p.discountedprice,p.category,p.quantitysold,p.productlikes,p.productrating,p.productratingamt,p.shippingtype,p.shipfrom FROM product p INNER JOIN store s ON p.storeid = s.storeid WHERE s.storename = 'somen.sg';")
#     fetchdata = cur.fetchall()
#     stripped_data = [[str(item).strip() for item in row] for row in fetchdata]
#     cur.close()
#     return render_template("tables.html", data=stripped_data)
# @app.route('/blank/<int:product_id>', methods=['GET'])
# def view_store(product_id):
#     cur = mysql.connection.cursor()
#     cur.execute("SELECT p.productid,p.ProductName,p.Productdesc,p.sellingprice,p.discountedprice,p.category,p.quantitysold,p.productlikes,p.productrating,p.productratingamt,p.shippingtype,p.shipfrom FROM product p INNER JOIN store s ON p.storeid = s.storeid WHERE p.productid = %s;", (product_id,))
#     fetchdata = cur.fetchall()

#     cur.close()
#     return render_template("blank.html", data=fetchdata)

# @app.route('/delete_product', methods=['POST'])
# def delete_product():
#     product_id = request.form.get('id')
#     print(product_id)
#     # Connect to MySQL
#     conn = mysql.connection
#     cursor = conn.cursor()

#     try:
#         # Execute the delete query
#         query = "DELETE FROM product WHERE productid = %s"
#         cursor.execute(query, (product_id,))
#         conn.commit()
#         return redirect('/success')
#     except Exception as error:
#         # Handle any errors that occur during the deletion
#         print(f"Error deleting product: {error}")
#         return redirect('/404')

#     finally:
#         # Close the cursor
#         cursor.close()




# @app.route('/update_product', methods=['POST'])
# def update_product():
#     # Retrieve the form data
#     id = request.form['id']
#     product_name = request.form['ProductName']
#     product_description = request.form['ProductDescription']
#     selling_price = decimal.Decimal(request.form['sellingPrice'])

#     discountPercentage = decimal.Decimal(request.form['discountPercentage'])
#     print(discountPercentage)
#     discounted_price = (selling_price*(100-discountPercentage))/100
#     quantity = request.form['Quantity']
#     free_shipping = request.form.get('freeShipping')  # Checkbox value

#     # Perform the update operation using the retrieved data and the ID
#     cur = mysql.connection.cursor()
#     sql = "UPDATE product SET productName = %s, productDesc = %s, sellingprice = %s, discountedprice = %s, quantitysold = %s, shippingtype = %s WHERE productId = %s"
#     params = (product_name, product_description, selling_price, discounted_price, quantity, free_shipping, id)

#     print("SQL Statement:", sql)
#     print("Parameters:", params)

#     cur.execute(sql, params)
    
#     print()
#     mysql.connection.commit()
#     cur.close()

#     # Redirect to a success page or perform any other necessary action
#     return redirect('/success')

@app.route('/success')
def success():
    return render_template('success.html')

@app.route('/index')
def compare():
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

# Buttons Page
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
