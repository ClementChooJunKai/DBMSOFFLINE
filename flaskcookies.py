from flask import Flask,make_response,request

app = Flask(__name__)

@app.route('/set')
def setCookie():
    respone =make_response("I have set the cookie")
    respone.set_cookie("myapp","Flask web Development")
    return respone

@app.route('/get')
def getCookie():
     myapp =request.cookies.get('myapp')
     return "The cookie content is " + myapp

if __name__ == "__main__":
    app.run(debug=True)