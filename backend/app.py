import os
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from plaid import ApiClient, Configuration
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.country_code import CountryCode
from plaid.model.products import Products

load_dotenv()

PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET")
PLAID_ENV = os.getenv("PLAID_ENV", "sandbox")

env_map = {
    "sandbox": "https://sandbox.plaid.com",
    "development": "https://development.plaid.com",
    "production": "https://production.plaid.com",
}

configuration = Configuration(
    host=env_map[PLAID_ENV],
    api_key={
        "clientId": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
    }
)
api_client = ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

app = Flask(__name__)
CORS(app)

# demo storage for now to be replaced by DB
ITEMS = {}

@app.route("/api/create_link_token", methods=["POST"])
def create_link_token():
    try:
        user_id = request.json.get("user_id", "user-123")

        link_token_request = LinkTokenCreateRequest(
            user={"client_user_id": user_id},
            client_name="My App",
            country_codes=[CountryCode('US')],
            language="en",
            products=[Products('transactions')]
        )

        response = client.link_token_create(link_token_request)
        return jsonify(response.to_dict())

    except Exception as e:
        print("create_link_token error:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/exchange_public_token", methods=["POST"])
def exchange_public_token():
    try:
        public_token = request.json.get("public_token")
        if not public_token:
            return jsonify({"error": "public_token required"}), 400

        exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
        exchange_response = client.item_public_token_exchange(exchange_request)

        access_token = exchange_response["access_token"]
        item_id = exchange_response["item_id"]

        # store the access token for later, just for demo rn
        ITEMS[item_id] = {
            "access_token": access_token,
            "item_id": item_id
        }

        return jsonify({"item_id": item_id})

    except Exception as e:
        print("exchange error:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/transactions", methods=["GET"])
def get_transactions():
    try:
        item_id = request.args.get("item_id")
        if not item_id:
            return jsonify({"error": "item_id required"}), 400

        item = ITEMS.get(item_id)
        if not item:
            return jsonify({"error": "Unknown item_id"}), 404

        access_token = item["access_token"]

        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)

        request_data = TransactionsGetRequest(
            access_token=access_token,
            start_date=start_date,
            end_date=end_date
        )

        response = client.transactions_get(request_data)

        accounts = [account.to_dict() for account in response["accounts"]]
        transactions = [txn.to_dict() for txn in response["transactions"]]

        return jsonify({
            "accounts": accounts,
            "transactions": transactions
        })

    except Exception as e:
        print("transactions error:", e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"Server running at http://localhost:{port}")
    app.run(port=port)
