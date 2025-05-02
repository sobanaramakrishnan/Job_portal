from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

# Upload config
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'resumes')
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__, template_folder='templates')

# App Config
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jobportals.db'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure resume upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database setup
db = SQLAlchemy(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    location = db.Column(db.String(100))
    salary = db.Column(db.String(50))
    employer_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seeker_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'))
    resume = db.Column(db.String(255))
    seeker = db.relationship('User', backref='applications')
    job = db.relationship('Job', backref='applications')

# User Loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please login.', 'warning')
            return redirect(url_for('login'))

        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_pw, role=role)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if not user:
            flash('Email not registered. Please sign up first.', 'danger')
            return redirect(url_for('login'))

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            if user.role == 'seeker':
                return redirect(url_for('seeker_dashboard'))
            elif user.role == 'employer':
                return redirect(url_for('employer_dashboard'))
            elif user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
        else:
            flash('Incorrect password.', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/seeker/dashboard')
@login_required
def seeker_dashboard():
    if current_user.role != 'seeker':
        return redirect(url_for('home'))

    category = request.args.get('category')
    location = request.args.get('location')

    query = Job.query
    if category:
        query = query.filter(Job.category.ilike(f"%{category}%"))
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))

    jobs = query.all()
    return render_template('seeker_dashboard.html', jobs=jobs)

@app.route('/apply/<int:job_id>', methods=['POST'])
@login_required
def apply_job(job_id):
    if current_user.role != 'seeker':
        return redirect(url_for('home'))

    resume = request.files['resume']
    if resume and allowed_file(resume.filename):
        filename = secure_filename(resume.filename)
        resume_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        resume.save(resume_path)

        application = Application(
            seeker_id=current_user.id,
            job_id=job_id,
            resume=filename
        )
        db.session.add(application)
        db.session.commit()  # <--- The INSERT happens here
        flash("Applied successfully!")

    return redirect(url_for('seeker_dashboard'))

@app.route('/resumes/<filename>')
@login_required
def download_resume(filename):
    resume_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(resume_path):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    else:
        flash("Resume file not found.", "danger")
        return redirect(url_for('seeker_dashboard'))

@app.route('/employer/dashboard', methods=['GET', 'POST'])
@login_required
def employer_dashboard():
    if current_user.role != 'employer':
        return redirect(url_for('home'))

    if request.method == 'POST':
        job = Job(
            title=request.form['title'],
            category=request.form['category'],
            location=request.form['location'],
            salary=request.form['salary'],
            description=request.form['description'],
            employer_id=current_user.id
        )
        db.session.add(job)
        db.session.commit()
        flash('Job posted!')

    jobs = Job.query.filter_by(employer_id=current_user.id).all()
    return render_template('employer_dashboard.html', jobs=jobs)

@app.route('/edit_job/<int:job_id>', methods=['POST'])
@login_required
def edit_job(job_id):
    if current_user.role != 'employer':
        return redirect(url_for('home'))

    job = Job.query.get_or_404(job_id)
    if job.employer_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('employer_dashboard'))

    job.title = request.form['title']
    job.category = request.form['category']
    job.location = request.form['location']
    job.salary = request.form['salary']
    job.description = request.form['description']
    db.session.commit()
    flash('Job updated!', 'success')
    return redirect(url_for('employer_dashboard'))

@app.route('/employer/delete_job/<int:job_id>')
@login_required
def employer_delete_job(job_id):
    if current_user.role != 'employer':
        return redirect(url_for('home'))

    job = Job.query.get_or_404(job_id)
    if job.employer_id != current_user.id:
        flash("Unauthorized!", "danger")
        return redirect(url_for('employer_dashboard'))

    db.session.delete(job)
    db.session.commit()
    flash("Job deleted.")
    return redirect(url_for('employer_dashboard'))

@app.route('/employer/delete_application/<int:application_id>', methods=['POST'])
@login_required
def employer_delete_application(application_id):
    if current_user.role != 'employer':
        flash("Unauthorized.", "danger")
        return redirect(url_for('home'))

    application = Application.query.get_or_404(application_id)
    job = Job.query.get(application.job_id)

    if job.employer_id != current_user.id:
        flash("Unauthorized to delete this application.", "danger")
        return redirect(url_for('employer_dashboard'))

    resume_path = os.path.join(app.config['UPLOAD_FOLDER'], application.resume)
    if os.path.exists(resume_path):
        os.remove(resume_path)

    db.session.delete(application)
    db.session.commit()
    flash("Application deleted successfully.", "success")
    return redirect(url_for('employer_dashboard'))

@app.route('/seeker/delete_application/<int:application_id>', methods=['POST'])
@login_required
def seeker_delete_application(application_id):
    application = Application.query.get_or_404(application_id)

    if application.seeker_id != current_user.id:
        flash("Unauthorized action.", "danger")
        return redirect(url_for('seeker_dashboard'))

    resume_path = os.path.join(app.config['UPLOAD_FOLDER'], application.resume)
    if os.path.exists(resume_path):
        os.remove(resume_path)

    db.session.delete(application)
    db.session.commit()
    flash("Application deleted successfully.", "success")
    return redirect(url_for('seeker_dashboard'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('home'))

    users = User.query.all()
    jobs = Job.query.all()
    return render_template('admin_dashboard.html', users=users, jobs=jobs)

@app.route('/admin/delete_user/<int:user_id>')
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('home'))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("User deleted.")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_job/<int:job_id>')
@login_required
def admin_delete_job(job_id):
    if current_user.role != 'admin':
        return redirect(url_for('home'))

    job = Job.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    flash("Job deleted.")
    return redirect(url_for('admin_dashboard'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, use_reloader=False)
   
    from os import environ
    app.run(host='0.0.0.0', port=int(environ.get("PORT", 5000)))


