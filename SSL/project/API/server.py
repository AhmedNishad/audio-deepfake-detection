from flask import Flask, jsonify, request, send_file
from pymongo import MongoClient
from bson import json_util, ObjectId
import json
import os
import speech_recognition as sr
from datetime import datetime
import sys

# Add the relative path to the parent directory of the model module to the system path
model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'model-WavLM'))
sys.path.append(model_path)

# Now you can import the SSLModel class from the model module
from model import SSLModel

import torch

app = Flask(__name__)

# Configuration
MONGO_URI = 'mongodb://localhost:27017/'
RECORDINGS_DIR = r'D:\Uni\FYP\Implementation\Code\SSL\API\recordings'

# Initialize MongoDB client
client = MongoClient(MONGO_URI)
db = client.flask_db
todos = db.todos

ssl_orig_output_dim = 1024  # Assuming this is the dimension of your model's output
ssl_model = SSLModel.load_model('trained_network.pt', ssl_orig_output_dim)

# model = ssl_model()
# model.load_state_dict(torch.load('trained_network.pt'))
# model.eval()

def transcribe_audio(audio_file_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file_path) as source:
        audio_data = recognizer.record(source)
    try:
        transcribed_text = recognizer.recognize_google(audio_data)
        return transcribed_text
    except sr.UnknownValueError:
        return None
    except sr.RequestError:
        return None

def save_audio_file(file):
    if file.filename == '':
        return None
    today = datetime.today()
    new_file_name = f"{today.timestamp()}{file.filename}"
    file_path = os.path.join(RECORDINGS_DIR, new_file_name)
    file.save(file_path)
    return new_file_name

def parse_mongo_data(data):
    return json.loads(json_util.dumps(data))

@app.route('/predict', methods=['POST'])
def predict():
    is_deepfake = True  # Placeholder for model prediction
    file = request.files['file']
    new_file_name = save_audio_file(file)
    if not new_file_name:
        return jsonify({'error': 'No selected file'})
    transcript = transcribe_audio(os.path.join(RECORDINGS_DIR, new_file_name))
    inserted_id = ""
    if is_deepfake:
        insert_result = todos.insert_one({'publicFigure': '', 'transcript': transcript, 'createdOn': datetime.today(), 'fileName': new_file_name})
        inserted_id = insert_result.inserted_id
    return jsonify(parse_mongo_data({'_id': inserted_id, 'isDeepfake': is_deepfake}))


@app.route('/attribute', methods=['POST'])
def attribute():
    resultId = request.json['id']
    publicFigure = request.json['publicFigure']
    result = db.todos.update_one({'_id': ObjectId(resultId)}, {"$set": {'publicFigure': publicFigure}})

    return result.raw_result

@app.route('/search', methods=['GET'])
def search():
    text = request.args['text']
    result = db.todos.find({"$or": [
    { 'publicFigure': { '$regex': text, '$options': 'i' } },
    { 'transcript': { '$regex': text, '$options': 'i' } }
    ]})
    print(result)
    return jsonify(parse_mongo_data(result))

@app.route('/detail', methods=['GET'])
def detail():
    resultId = request.args['id']
    result = db.todos.find({ '_id' : ObjectId(resultId) })
    print(result)
    return jsonify(parse_mongo_data(result))

@app.route('/stream-audio/')
def streamAudio():
    fileName = request.args['fileName']
    try:
        return send_file(os.path.join(RECORDINGS_DIR, fileName))
    except Exception as e:
        return str(e)

# Other routes...

if __name__ == '__main__':
    app.run()


