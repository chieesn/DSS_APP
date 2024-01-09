from flask import Flask, request, jsonify, render_template, redirect, url_for
import json
from pymongo import MongoClient
from bson import ObjectId
from gridfs import GridFS
from PIL import Image, ImageDraw, ImageFont
import requests
import uuid
import io

app = Flask(__name__)

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['imageDB']
myCollection = db["IN_1"]

#clear database
#myCollection.delete_many({}) 
save_path = "./static/{}.JPEG"
def get_uuid_id():

    return str(uuid.uuid4())
 


@app.route('/')
def home():
    return render_template('./main.html')

@app.route('/scanning')
def scan():
    return render_template('./index.html')
# Route for image upload
@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    image_file = request.files['image']

    uuid = get_uuid_id()
    image_path = save_path.format(uuid)
    image_file.save(image_path)

    image_file = open(image_path, 'rb')
    
    img_draw = Image.open(image_path)
    draw = ImageDraw.Draw(img_draw)
    #font = ImageFont.load_default()
    new_font = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeSerif.ttf',size=120)

    # Mocked API call for image processing (replace with actual API endpoint)
    predict_url = 'http://140.138.172.215:5000/predict'
    processed_data = requests.post(predict_url, files={'image': image_file})
    print(processed_data.json())
    typeOfCancer = processed_data.json()['typeOfCancer']


    image_width, image_height = img_draw.size
    text_width, text_height = draw.textsize(typeOfCancer, font=new_font)
    margin = 10
    position = (image_width - text_width - margin, image_height - text_height - margin)
    text_color = (0, 0, 0)
    draw.text(position, typeOfCancer, font=new_font, fill=text_color)
    img_draw.save(image_path)

    record = {
        "img_path": uuid,
        "typeOfCancer": processed_data.json()['typeOfCancer'],
        "dist": processed_data.json()['dist']
    }
    result = myCollection.insert_one(record)
    print(result.inserted_id)
    return jsonify({
        'message': 'Image uploaded and processed',
        'file_id': str(result.inserted_id),
        'typeOfCancer' : typeOfCancer,
        'processed_data': processed_data.json() if processed_data.status_code == 200 else None
    }), 200

@app.route('/list')
def get_list():
    cursor = myCollection.find()
    result = []
    if cursor:
        for record in cursor:
            result.append(record)

        return render_template('list.html', result=result)
    else:
        return None, 200

@app.route('/retrieve')
def get_record():
    image_id = request.args.get('_id')
    
    record_id = ObjectId(image_id)
    result = myCollection.find_one({"_id":record_id})
    if result:
        data = {
            'label': [],
            'value': [],
            'color': [
                '#FF6384', # Red
                '#36A2EB', # Blue
                '#FFCE56', # Yellow
                '#4BC0C0', # Turquoise
                '#9966FF', # Purple
                '#FF9F40', # Orange
                '#66CC99'  # Green
            ]
        }
        for (label, value) in result['dist'].items():
            data['label'].append(label)
            data['value'].append(value)
        return json.dumps(data), 200
    else:
        return None, 200


if __name__ == '__main__':
    app.run(debug=True)
