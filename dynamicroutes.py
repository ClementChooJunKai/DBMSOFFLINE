from flask import Flask

app = Flask(__name__)

@app.route('/')
def Index():
    return "Hello Index Page"

@app.route('/contact/<name>')
def Contact(name):
     return "Hello Contact Page Mr %s " %name

if __name__ == "__main__":
    app.run(debug=True)