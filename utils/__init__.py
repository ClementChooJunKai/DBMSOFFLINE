# utils.py

from collections import Counter
import decimal
import pandas as pd
from statsmodels.tsa.holtwinters import SimpleExpSmoothing
from itertools import count
import nltk
from nltk.tokenize import word_tokenize
import re

# Database Helper Functions (move functions from helpers.database here)
from helpers.database import *
from helpers.hashpass import *

# Function to configure the Flask app and setup MySQL
def configure_app(app):
    app.secret_key = "ITSASECRET"
    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = 'root'
    app.config['MYSQL_DB'] = 'dbms'

    return app
