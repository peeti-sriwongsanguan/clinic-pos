from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/api/patients', methods=['GET'])
def get_patients():
    # Implementation
    pass

@app.route('/api/services', methods=['GET'])
def get_services():
    # Implementation
    pass