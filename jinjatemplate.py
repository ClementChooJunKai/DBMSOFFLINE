from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def Index():
    context ={
        "data":"This is data from index",
        "name":"Bob"
    }
    name = "John Doe"
    return render_template('index.html',mydata = context)

@app.route('/compare')
def compare():
    return render_template('compare.html')

if __name__ == "__main__":
    app.run(debug=True)