from flask import Flask, render_template, request, url_for, redirect, flash, session
from flask_sqlalchemy import SQLAlchemy, SessionBase
from flask_login import LoginManager, UserMixin, login_user
from wtforms import Form, StringField, PasswordField, BooleanField, validators
from passlib.hash import sha256_crypt
from flask_bootstrap import Bootstrap

app = Flask(__name__)
Bootstrap(app)

app.secret_key = 'my unobvious secret key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@localhost/healthyhabits'

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

class Users(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(200))
	email = db.Column(db.String(200))
	password = db.Column(db.String(200))

class Nutrients(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer)
	calories = db.Column(db.Integer)
	fats = db.Column(db.Integer)
	cholesterol = db.Column(db.Integer)
	carbohydrates = db.Column(db.Integer)
	proteins = db.Column(db.Integer)

class TotalNutrients():
	calories = 0
	fats = 0
	cholesterol = 0
	carbohydrates = 0
	proteins = 0

class UserMetrics(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer)
	weight = db.Column(db.Float)
	height = db.Column(db.Float)
	age = db.Column(db.Integer)
	gender = db.Column(db.Integer)

class RecommendedIntake(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer)
	calories = db.Column(db.Integer)
	fats = db.Column(db.Integer)
	cholesterol = db.Column(db.Integer)
	carbohydrates = db.Column(db.Integer)
	proteins = db.Column(db.Integer)

class RegistrationForm(Form):
	username = StringField('Username')
	email = StringField('Email Address')
	password = PasswordField('Password', {validators.DataRequired(),
										  validators.EqualTo('confirm', message="Passwords must match")})
	confirm = PasswordField('Confirm Password')
	acceptTos = BooleanField('I accept the Terms of Service',
							 [validators.DataRequired()])

class LoginForm(Form):
	username = StringField('Username', [validators.InputRequired()])
	password = PasswordField('Password', [validators.InputRequired()])
	remember = BooleanField('Remember')

class NutrientsForm(Form):
	calories = StringField('Calories')
	fats = StringField('Fats')
	cholesterol = StringField('Cholesterol')
	carbohydrates = StringField('Carbohydrates')
	proteins = StringField('Proteins')

class MetricsForm(Form):
	weight = StringField('Weight')
	height = StringField('Height')
	age = StringField('Age')
	gender = StringField('Gender')


@login_manager.user_loader
def load_user(user_id):
	return Users.query.get(int(user_id))

@app.route('/register', methods =['GET','POST'])
def register():
	form = RegistrationForm(request.form)
	if request.method == "POST" and form.validate():
		newUsername = form.username.data
		newEmail = form.email.data
		newPassword = sha256_crypt.encrypt(str(form.password.data))
		query = Users.query.filter(Users.username == newUsername).first()

		if query is not None:
			flash("Username is taken")
			return render_template('register.html', form = form)
		else:
			user = Users(username = newUsername, email = newEmail, password = newPassword)
			db.session.add(user)
			db.session.commit()
			flash("Registration Successful!")
			session['logged_in'] = True
			session['username'] = newUsername
			return redirect(url_for('index'))

	return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
	form = LoginForm(request.form)
	if form.validate():
		user = Users.query.filter(Users.username == form.username.data).first()
		if user:
			if sha256_crypt.verify(str(form.password.data), str(user.password)):
				session['username'] = user.username
				return "Logged in!"
	return render_template('login.html', form=form)

@app.route('/')
def index():
	return 'Hello!'

@app.route('/addNutrients', methods=['GET','POST'])
def add_nutrients():
	user = Users.query.filter(Users.username == session['username']).first()
	form = NutrientsForm(request.form)
	logs = Nutrients.query.filter(Nutrients.user_id == user.id).all()

	total_cal = 0
	total_carbs = 0
	total_fats = 0
	total_proteins = 0

	for log in logs:
		total_cal += log.calories
		total_carbs += log.carbohydrates
		total_fats += log.fats
		total_proteins += log.proteins

	total = TotalNutrients()

	total.calories = total_cal
	total.carbohydrates = total_carbs
	total.fats = total_fats
	total.proteins = total_proteins
	
	print(total)

	if request.method == "POST" and form.validate():
		calories = form.calories.data
		fats = form.fats.data
		cholesterol = form.cholesterol.data
		carbohydrates = form.carbohydrates.data
		proteins = form.proteins.data

		nutrients = Nutrients(user_id = int(user.id), calories = int(calories), fats = int(fats), 
							  cholesterol = int(cholesterol), carbohydrates = int(carbohydrates),
							  proteins = int(proteins))

		print(logs)

		db.session.add(nutrients)
		db.session.commit()
	return render_template('index.html', form=form, logs=logs, total = total)

@app.route('/calculateCalories', methods=['GET','POST'])
def calculate_calories():
	form = MetricsForm(request.form)
	if request.method == "POST" and form.validate():
		weight = form.weight.data
		height = form.height.data
		age = form.age.data

		user = Users.query.filter(Users.username == session['username']).first()

		metrics = UserMetrics(user_id = int(user.id), weight = int(weight), height = int(height), 
							  age = int(age), gender = 1)

		calories_per_day = (10 * int(weight)) + (6.25 * int(height)) - (5 * int(age)) + 5

		rec_carbs = calories_per_day * .5
		rec_fats = (calories_per_day * .3) / 9
		rec_protein = (calories_per_day * .2) / 4

		rec_intake = RecommendedIntake(user_id = int(user.id), calories = int(calories_per_day), fats = int(rec_fats), 
							  cholesterol = int(0), carbohydrates = int(rec_carbs),
							  proteins = int(rec_protein))

		db.session.add(rec_intake)
		db.session.add(metrics)
		db.session.commit()
	return render_template('calculate.html', form=form)

if __name__ == 'main':
	url = 'http://127.0.0.1:5000'
	app.config['SESSION_TYPE'] = 'filesystem'
	app.run(debug = True)