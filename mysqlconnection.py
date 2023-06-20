from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL

app = Flask(__name__)

# Configure MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'dbms'

# Create MySQL instance
mysql = MySQL(app)

@app.route('/')
def home():
    cur = mysql.connection.cursor()
    cur.execute("SELECT storeName FROM sellers WHERE id = 1")
    fetchdata = cur.fetchall()
    store_name = str(fetchdata[0]).strip("(''',)")
    cur.close()
    return render_template("home.html", data=store_name)

# Tables Page
@app.route('/tables', methods=["GET"])
def tables():
    cur = mysql.connection.cursor()
    cur.execute("SELECT storeName FROM sellers WHERE id = 1")
    fetchdata = cur.fetchall()
    store_name = str(fetchdata[0]).strip("(''',)")
    cur.close()
    return render_template("tables.html",data=store_name)

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
        # registerUser()
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
