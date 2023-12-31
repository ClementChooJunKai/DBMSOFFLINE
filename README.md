# Admin Arcade: A Comprehensive Database Solution

## INF2003 Database Project Description

Admin Arcade is a comprehensive database solution that aims to provide e-commerce sellers with a powerful platform to manage their products, stores, accounts, and user data. The system utilizes both SQL and MongoDB databases to efficiently store and manage different types of data. This project is developed by Group Number 2, comprising the following members:

- Darren Lee Cheng Wai (ID: 2201220)
- Tan Wen Jie Nicolas (ID: 2203432)
- Veleon Lim Ming Zhe (ID: 2201947)
- Clement Choo Jun Kai (ID: 2202587)
- Shaun Tay Jia Le (ID: 2200555)

## Getting Started

1. Install Dependencies: Begin by installing the required dependencies listed in the `requirements.txt` file using the terminal command:

   ```
   pip install -r requirements.txt
   ```

2. Setup SQL Database:
   - Execute the SQL script `sql_script.sql` in the terminal to create the necessary tables. Replace `{username}` with your SQL username:

     ```
     mysql -u {username} -p < sql_script.sql
     ```

   - Import the data files in CSV format into the SQL database using the following table names:
     - `store`: store.csv
     - `product`: product.csv
     - `account`: account.csv

3. Setup MongoDB:
   - Create a MongoDB database named `userData`.
   - Within the `userData` database, create the following collections:
     - `order`
     - `product`
     - `store`
     - `user`

   - Import the data files in JSON format into the corresponding MongoDB collections:
     - `order`: userData.order.json
     - `product`: userData.product.json
     - `store`: userData.store.json
     - `user`: userData.user.json

4. Modify SQL Credentials: Update the SQL credentials in the `/utils/__init__.py` file (Line 24-29) with your MySQL host, username, and password:

   ```
   app.config['MYSQL_HOST']
   app.config['MYSQL_USER']
   app.config['MYSQL_PASSWORD']
   ```

5. Install NLTK (First Time Execution):
   - Uncomment the line `nltk.download()` in `app.py` (Line 33) for the first-time program execution. This installs NLTK used for optimization.
   
   - For subsequent executions, comment out the line `nltk.download()` in `app.py` (Line 33).
     
7. Update DB user namename,password and database for langchain implementation:
   - in `products.py` line 414 => db = SQLDatabase.from_uri("mysql+pymysql://root:root@localhost/dbms")
   - update to your appropriate username,password and database "username:password@localhost/database_name"
 
8. Run the Program:
   Execute `app.py` to run the program.
   If module not loaded on execute, change 'App.py' to 'app.py'

9. Test Account Credentials:
   Use the following test account to explore the system:
   - Username: adidassg
   - Password: test

   We have disabled the otp in order to allow easier testing with the test account
   To enable Otp go to _init_.py line 35 to enable

