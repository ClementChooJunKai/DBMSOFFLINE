from flask import Flask, Blueprint, render_template, request, redirect, url_for, session
from model import *
from utils import *

revenue_blueprint = Blueprint('revenue', __name__)


@revenue_blueprint.route('/revenue', methods=['GET', 'POST'])
def revenue_page():
    if 'username' in session:
        username = session['username']

        # Aggregate pipeline to calculate revenue
        revenue_pipeline = [
            {
                '$lookup': {
                    'from': 'store',
                    'localField': 'storeId',
                    'foreignField': 'StoreID',
                    'as': 'store'
                }
            },
            {
                '$match': {
                    'store.storeName': username
                }
            },
            {
                '$project': {
                    '_id': 0,
                    'quantitySold': 1,
                    'discountedPrice': 1,
                    'productName': 1,
                    'revenue': {'$multiply': ['$quantitySold', '$discountedPrice']},
                    'StoreID': 1,
                }
            }
        ]

        # Aggregate pipeline to calculate total quantity sold
        quantity_sold_pipeline = [
            {
                '$lookup': {
                    'from': 'store',
                    'localField': 'storeId',
                    'foreignField': 'StoreID',
                    'as': 'store'
                }
            },


            {

                '$match': {
                    'store.storeName': username
                }
            },
            {
                '$sort': {
                    'quantitySold': -1
                }
            },
            {
                '$limit': 10
            },
            {
                '$project': {
                    '_id': 0,
                    'productName': 1,
                    'totalQuantitySold': '$quantitySold'
                }
            }
        ]
    
        each_product_sold_pipeline = [
    {
        '$lookup': {
            'from': 'product',
            'localField': 'ProductID',
            'foreignField': 'productId',
            'as': 'product'
        }
    },
    {
        '$unwind': '$product'
    },
    {
        '$lookup': {
            'from': 'store',
            'localField': 'StoreID',
            'foreignField': 'StoreID',
            'as': 'store'
        }
    },
    {
        '$unwind': '$store'
    },
    {
        '$match': {
            'store.storeName': username  # Replace "store_username" with the actual store name
        }
    },
    {
        '$group': {
            '_id': {
                
                'year': {'$year': {'$dateFromString': {'dateString': '$Date', 'format': '%d/%m/%Y'}}},
                'month': {'$month': {'$dateFromString': {'dateString': '$Date', 'format': '%d/%m/%Y'}}},
                'productId': '$product.productId',
            },
            'quantitySold': {'$sum': '$Quantity'},  
            'productName': {'$first': '$product.productName'},
            'storeName': {'$first': '$store.storeName'},
        }
    },
    {
        '$project': {
            '_id': 0,
            'year': '$_id.year',
            'month': '$_id.month',
            'productId': '$_id.productId',
            'quantitySold': 1,
            'productName': 1,
            'storeName': 1,
        }
    },
    {
        '$sort': {
            'year': 1,
            'month': 1
        }
    }
]

   


    goal_pipeline = [
        {
            '$lookup': {
                'from': 'product',
                'localField': 'ProductID',
                'foreignField': 'productId',
                'as': 'product'
            }
        },
        {
            '$unwind': '$product'
        },
        {
            '$lookup': {
                'from': 'store',
                'localField': 'StoreID',
                'foreignField': 'StoreID',
                'as': 'store'
            }
        },
        {
            '$unwind': '$store'
        },
        {
            '$group': {
                '_id': {
                    'year': {'$year': {'$dateFromString': {'dateString': '$Date', 'format': '%d/%m/%Y'}}},
                    'month': {'$month': {'$dateFromString': {'dateString': '$Date', 'format': '%d/%m/%Y'}}}
                },
                'totalSales': {'$sum': {'$multiply': ['$Quantity', '$Price']}}
            }
        },
        {
            '$project': {
                '_id': 0,
                'year': '$_id.year',
                'month': '$_id.month',
                'totalSales': 1
            }
        },
        {
            '$sort': {
                'year': 1,
                'month': 1
            }
        }
    ]

    revenue_data = list(db.product.aggregate(revenue_pipeline))
    quantity_sold_data = list(db.product.aggregate(quantity_sold_pipeline))
    each_product_sold_data = list(
        db.order.aggregate(each_product_sold_pipeline))
    goal_data = list(db.order.aggregate(goal_pipeline))
    for product_data in each_product_sold_data:
        print(product_data)
    sales_per_month = 0
    last_month = 0
    months_to_goal = 0
    combined_data_str_keys = 0
    
    

    if request.method == 'POST':
        # Get the input data from the form
        target_sales = int(request.form.get('targetSales'))
        months_to_goal = int(request.form.get('monthsToGoal'))

        # Calculate the remaining sales needed for the target
        current_total_sales = sum(item['totalSales'] for item in goal_data)
        last_month = f"{goal_data[-1]['month']:02d}"
        remaining_sales_needed = target_sales - current_total_sales

        # Calculate the sales required per month to reach the target
        sales_per_month = remaining_sales_needed / months_to_goal

        # Manually convert 'year' and 'month' to strings in 'YYYY-MM' format
        for item in goal_data:
            year_month = f'{item["year"]:02d}-{item["month"]:02d}'
            item['Date'] = pd.to_datetime(year_month, format='%y-%m')

        # Convert the data to a Pandas DataFrame
        df = pd.DataFrame(goal_data)
        df.set_index('Date', inplace=True)
        df.drop(['year', 'month'], axis=1, inplace=True)

        # Provide the frequency information explicitly for the DataFrame index
        df.index.freq = 'MS'

        # Create a Simple Exponential Smoothing model
        model = SimpleExpSmoothing(df['totalSales'])

        # Fit the model
        results = model.fit()

        # Forecast future values
        # Number of steps to forecast (equal to months_to_goal)
        forecast_steps = months_to_goal
        forecast = results.forecast(steps=forecast_steps)

        # Create a new DataFrame with the forecasted totalSales
        forecast_df = pd.DataFrame(forecast, index=pd.date_range(
            start=df.index[-1] + pd.DateOffset(months=1), periods=forecast_steps, freq='MS'), columns=['totalSales'])

        # Combine the original data and the forecasted data
        combined_data = pd.concat([df, forecast_df])

        # Your Flask route or function
        combined_data = combined_data.to_dict(orient='index')
        combined_data_str_keys = {key.strftime(
            '%Y-%m-%d'): value for key, value in combined_data.items()}

        print(combined_data_str_keys)

    return render_template("revenue/revenue.html", revenue_data=revenue_data, username=username,  quantity_sold_data=quantity_sold_data,  each_product_sold_data=each_product_sold_data, goal_data=goal_data, sales_per_month=sales_per_month, last_month=last_month, months_to_goal=months_to_goal, combined_data=combined_data_str_keys)


if __name__ == "__main__":
    app.run(debug=True)
