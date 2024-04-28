from flask import Flask, jsonify, request
import numpy as np
import pandas as pd
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DATA = "../data.csv"
data = pd.read_csv(DATA)
data = data.dropna()
data['discount'] = (data['original_price'] - data['selling_price']) / data['original_price'] * 100
data['discount'] = data['discount'].astype(int)

@app.route('/', methods=['GET'])
def get_discount_vs_rating():
    level = request.args.get('level', default=0, type=int)
    name = request.args.get('name', default='', type=str)
    number = request.args.get('number', default=0, type=int)
    number = int(number)
    rating = request.args.get('rating', default=3.5, type=float)
    discount = request.args.get('discount', default=0, type=float)

    

    number = True if number == 1 else False

    
    rating_threshold = float(rating)
    discount_threshold = float(discount)

    print(rating_threshold, discount_threshold)

    if level == 0:
        D = data.groupby('brand').aggregate({'discount': 'mean', 'product_rating': 'mean'})
    elif level == 1:
        D = data.where(data['category'] == name).groupby('brand').aggregate({'discount': 'mean', 'product_rating': 'mean'})
    elif level == 2:
        D = data.where(data['product_subcategory'] == name).groupby('brand').aggregate({'discount': 'mean', 'product_rating': 'mean'})
    elif level == 3:
        D = data.where(data['product_type'] == name).groupby('brand').aggregate({'discount': 'mean', 'product_rating': 'mean'})            

    
    # Filter based on rating_threshold and discount_threshold
    high_discount_high_rating = D[(D['discount'] > discount_threshold) & (D['product_rating'] > rating_threshold)]
    low_discount_low_rating = D[(D['discount'] <= discount_threshold) & (D['product_rating'] <= rating_threshold)]
    high_discount_low_rating = D[(D['discount'] > discount_threshold) & (D['product_rating'] <= rating_threshold)]
    low_discount_high_rating = D[(D['discount'] <= discount_threshold) & (D['product_rating'] > rating_threshold)]
    
    
    return jsonify({
        "data": D.to_dict(),
        "numbers": [len(high_discount_high_rating), len(high_discount_low_rating), len(low_discount_low_rating), len(low_discount_high_rating)]
    })

@app.route('/p', methods=['GET'])
def get_price_vs_rating():
    level = request.args.get('level', default=0, type=int)
    name = request.args.get('name', default='', type=str)
    number = request.args.get('number', default=0, type=int)
    number = int(number)
    rating = request.args.get('rating', default=3.5, type=float)
    price = request.args.get('price', default=0, type=float)

    

    number = True if number == 1 else False

    
    rating_threshold = float(rating)
    price_threshold = float(price)

    print(rating_threshold, price_threshold)

    if level == 0:
        D = data.groupby('brand').aggregate({'selling_price': 'mean', 'product_rating': 'mean'})
    elif level == 1:
        D = data.where(data['category'] == name).groupby('brand').aggregate({'selling_price': 'mean', 'product_rating': 'mean'})
    elif level == 2:
        D = data.where(data['product_subcategory'] == name).groupby('brand').aggregate({'selling_price': 'mean', 'product_rating': 'mean'})
    elif level == 3:
        D = data.where(data['product_type'] == name).groupby('brand').aggregate({'selling_price': 'mean', 'product_rating': 'mean'})            

    
    # Filter based on rating_threshold and discount_threshold
    high_discount_high_rating = D[(D['selling_price'] > price_threshold) & (D['product_rating'] > rating_threshold)]
    low_discount_low_rating = D[(D['selling_price'] <= price_threshold) & (D['product_rating'] <= rating_threshold)]
    high_discount_low_rating = D[(D['selling_price'] > price_threshold) & (D['product_rating'] <= rating_threshold)]
    low_discount_high_rating = D[(D['selling_price'] <= price_threshold) & (D['product_rating'] > rating_threshold)]
    
    
    return jsonify({
        "data": D.to_dict(),
        "numbers": [len(high_discount_high_rating), len(high_discount_low_rating), len(low_discount_low_rating), len(low_discount_high_rating)]
    })

@app.route('/h', methods=['GET'])
def get_heatmap():
    # Take Product Subcategory
    subcategory = request.args.get("subcategory", default='', type=str)
    print(subcategory)
    # Group by Brand
    D = data.groupby('brand').agg(
        product_subcategory=('product_subcategory', 'first'), 
        product_type_count=('product_type', 'count'), 
        product_rating_mean=('product_rating', 'mean')
    )

    # Extract Brands with more than 5 products
    D = D[D.product_type_count > 5]

    # Assign Bins
    num_bins = 5
    DS = D[D['product_subcategory'] == subcategory].copy()
    if DS.empty:
        return
    DS['rating_bin'] = pd.qcut(DS['product_type_count'], q=num_bins, labels=False, duplicates='drop') + 1  # Labels=False for easier manipulation

    # Check the distribution of counts per bin
    bin_counts = DS['rating_bin'].value_counts()
    max_length = bin_counts.max()

    # Increment the num_bins and do qcut if the max length of bin is greater than 7
    while max_length > 7 and num_bins < 9:
        num_bins += 1
        DS['rating_bin'] = pd.qcut(DS['product_type_count'], q=num_bins, labels=False, duplicates='drop') + 1
        bin_counts = DS['rating_bin'].value_counts()
        max_length = bin_counts.max()

    # After final binning, assign proper labels
    DS['rating_bin'] = pd.Categorical(DS['rating_bin'], categories=np.arange(1, num_bins+1))

    # In a Bin, sort the brands on the basis of rating, and assign serial numbers to each brand
    DS = DS.sort_values(['rating_bin', 'product_rating_mean'], ascending=[True, False])
    DS['brand_serial'] = DS.groupby('rating_bin').cumcount() + 1
    DS = DS.drop(columns=['product_subcategory'])
    DS['brand_name'] = DS.index
    max_rating = DS['product_rating_mean'].max()
    min_rating = DS['product_rating_mean'].min()
    return [DS.to_dict(orient='records'), {'num_bins': str(num_bins), 'max_length': str(max_length), 'max_rating': str(max_rating), 'min_rating': str(min_rating)}]

if __name__ == '__main__':
    app.run(debug=True)


