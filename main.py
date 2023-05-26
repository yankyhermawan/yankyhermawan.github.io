from flask import Flask, jsonify, request, make_response
from service.dbService import CreateConnection
import service.osmService as osmService
from flask_cors import CORS
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)
connection = CreateConnection()
port = os.environ.get("PORT") or 5000


@app.route("/api/getall", methods = ["GET"])
def index():
    data = connection.getAll()
    return data

@app.route("/api/data", methods = ["POST"])
def get_city_data():
    request_body = request.get_json()
    city = request_body["city"]
    height = request_body["height"]
    width = request_body["width"]
    response = {
        "data": osmService.scenario_data(city=city, h=height, w=width)
    }
    return jsonify(response)
        


app.run(port=port)