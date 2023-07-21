from flask import Flask, Blueprint, render_template, request, redirect, url_for, session
from model import *
from utils import *



category_blueprint = Blueprint('category', __name__)
@category_blueprint.route('/getCatP')
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

    return render_template('category/catProducts.html', main_categories=main_categories, sub_categories=sub_categories)



@category_blueprint.route('/get-product-cat', methods=["GET"])
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
        serialized_row = [str(item) if isinstance(item, decimal.Decimal) else item for item in row]
        serialized_data.append(serialized_row)

    # Return JSON response
    return json.dumps(serialized_data)


    # Redirect to a success page or perform any other necessary action
    