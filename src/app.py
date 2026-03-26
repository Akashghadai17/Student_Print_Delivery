from flask import Flask, render_template, request, redirect
from db import orders
import os, time
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf', 'ppt', 'pptx', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/order', methods=['GET', 'POST'])
def order():
    if request.method == 'POST':

        name = request.form['name']
        mobile = request.form['mobile']
        address = request.form['address']
        copies = int(request.form['copies'])
        color = request.form['color']

        files = request.files.getlist('file')

        total_pages = 0
        filenames = []

        for file in files:
            if file and allowed_file(file.filename):
                filename = str(int(time.time())) + "_" + secure_filename(file.filename)
                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(path)
                filenames.append(filename)

                if filename.endswith('.pdf'):
                    reader = PdfReader(path)
                    total_pages += len(reader.pages)
                else:
                    total_pages += 1

        if color == "Black & White":
            amount = total_pages * copies * 2
        else:
            amount = total_pages * copies * 10

        return render_template('payment.html',
                               name=name,
                               mobile=mobile,
                               address=address,
                               pages=total_pages,
                               copies=copies,
                               color=color,
                               amount=amount)

    return render_template('order.html')


@app.route('/confirm', methods=['POST'])
def confirm():
    data = request.form

    orders.insert_one({
        "name": data['name'],
        "mobile": data['mobile'],
        "address": data['address'],
        "pages": data['pages'],
        "copies": data['copies'],
        "color": data['color'],
        "amount": data['amount'],
        "time": time.strftime("%Y-%m-%d %H:%M:%S")
    })

    return redirect('/success')


@app.route('/success')
def success():
    return render_template('success.html')


if __name__ == "__main__":
    app.run(debug=True)