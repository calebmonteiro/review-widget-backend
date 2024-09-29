from flask import Flask, request, jsonify
from inference import get_product_and_description_from_url, get_questions_for_product  # Import your AI generation function
from product import insert_if_not_exists, connect_to_mongo, find_by_url  # MongoDB functions

app = Flask(__name__)

@app.route('/process_product', methods=['POST'])
def process_product():
    """Process the product URL: scrape if not in DB, then retrieve and return questions."""
    data = request.json
    product_url = data.get('url')

    if not product_url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        # Step 1: Connect to MongoDB
        client = connect_to_mongo()
        if not client:
            return jsonify({"error": "Failed to connect to MongoDB"}), 500

        # Step 2: Check if the product already exists in MongoDB
        existing_product = find_by_url(client, 'review-db', 'products', product_url)

        if not existing_product:
            # Step 3: scrape product and description
            prod_entry = get_product_and_description_from_url(product_url)
            if not prod_entry:
                return jsonify({"error": "Failed to scrape product info"}), 500

            # Step 4: Use AI to generate additional info
            document = get_questions_for_product(prod_entry)

            # Step 5: Insert the new product into MongoDB
            insert_result, insert_status_code = insert_if_not_exists(client, 'review-db', 'products', document)
            if insert_status_code != 201:
                return jsonify({"error": "Failed to insert new product"}), 500

        # Step 7: Retrieve the product again (whether it was inserted or already existed)
        product = find_by_url(client, 'review-db', 'products', product_url)
        if not product or 'questions' not in product:
            return jsonify({"error": "Product not found or no questions available"}), 500

        # Step 8: Extract the first 3 questions using keys like q1, q2, q3
        questions_field = product.get('questions', {})
        questions = [questions_field.get(f'q{i}') for i in range(1, 4) if questions_field.get(f'q{i}')]

        return jsonify({"questions": questions})

    except Exception as e:
        print(f"Error processing the product: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5000, debug=True)
