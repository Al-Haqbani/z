from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bugbrogram.db'
app.config['SECRET_KEY'] = os.urandom(24)
db = SQLAlchemy(app)

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    bounty_percentage = db.Column(db.Integer, default=5)  # 5% fee

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    reward = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default='open')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        hashed_pw = generate_password_hash(password)
        company = Company(name=name, email=email, password=hashed_pw)
        db.session.add(company)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        company = Company.query.filter_by(email=email).first()
        if company and check_password_hash(company.password, password):
            session['company_id'] = company.id
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'company_id' not in session:
        return redirect(url_for('login'))
    submissions = Submission.query.filter_by(company_id=session['company_id']).all()
    return render_template('dashboard.html', submissions=submissions)

@app.route('/submit', methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        company_id = request.form['company_id']
        title = request.form['title']
        description = request.form['description']
        reward = float(request.form['reward'])
        submission = Submission(company_id=company_id, title=title, description=description, reward=reward)
        db.session.add(submission)
        db.session.commit()
        return redirect(url_for('index'))
    companies = Company.query.all()
    return render_template('submit.html', companies=companies)

@app.route('/logout')
def logout():
    session.pop('company_id', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
