from flask import Flask, render_template, request, redirect, session, url_for
from db import orders
from pymongo import MongoClient
import os, time
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader

app = Flask(__name__)
app.secret_key = "secret123"

# 🔗 MongoDB (for users)
client = MongoClient("mongodb://localhost:27017/")
db = client["student_print_db"]
users = db["users"]

# 📁 Upload folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf', 'ppt', 'pptx', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 🏠 Home (Protected)
@app.route('/')
def index():
    if "user" not in session:
        return redirect('/login')
    return render_template('index.html', username=session["user"])

# 🔐 Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        user = users.find_one({"username": username, "password": password})

        if user:
            session["user"] = username
            return redirect('/')
        else:
            return "<h3>❌ Invalid Username or Password</h3>"

    return render_template('login.html')

# 📝 Signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        if users.find_one({"username": username}):
            return "<h3>⚠️ Username already exists</h3>"

        users.insert_one({
            "username": username,
            "password": password
        })

        return redirect('/login')

    return render_template('signup.html')

# 🚪 Logout
@app.route('/logout')
def logout():
    session.pop("user", None)
    return redirect('/login')

# 📄 Order Page (Protected)
@app.route('/order', methods=['GET', 'POST'])
def order():
    if "user" not in session:
        return redirect('/login')

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

# ✅ Confirm Order
@app.route('/confirm', methods=['POST'])
def confirm():
    if "user" not in session:
        return redirect('/login')

    data = request.form

    orders.insert_one({
        "username": session["user"],  # 🔥 linked to login user
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

# 🎉 Success Page
@app.route('/success')
def success():
    if "user" not in session:
        return redirect('/login')
    return render_template('success.html')

# ▶️ Run
if __name__ == "__main__":
    app.run(debug=True)
