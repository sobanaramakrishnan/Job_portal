# Job Portal – Employer Dashboard

This is a Flask-based web application where employers can post job openings, edit or delete them, and manage job applications submitted by job seekers. Applicants can upload their resumes, which the employer can view or delete.

---

## Features

* Employer dashboard to post new jobs
* List and manage posted jobs
* Edit job details using Bootstrap modals
* View job applicants and their resume files
* Delete individual applications
* Responsive design using Bootstrap 5

---

## Local Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/sobana/job-portal.git
cd job-portal
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate the virtual environment:

  ```bash
  venv\Scripts\activate
  ```

### 3. Install the Requirements

```bash
pip install -r requirements.txt
```

### 4. Run the Flask Application

```bash
python app.py
```

The app will run at: `http://127.0.0.1:5000/`

---

## requirements.txt

Create this file with:

```txt
Flask==2.2.5
gunicorn==21.2.0
```

Add other packages like `Flask-SQLAlchemy`, `python-dotenv`, etc., if used.

---

## Deployment on Render

### 1. Create a GitHub Repo and Push Code

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/job-portal.git
git push -u origin main
```

### 2. Prepare Render Files

#### `Procfile`:

```
web: gunicorn app:app
```

> Make sure your Flask app is in `app.py` and the instance is called `app`.

#### `requirements.txt`:

Already created earlier.

### 3. Deploy on Render

1. Go to [https://render.com](https://render.com)

2. Click **New Web Service**

3. Connect your GitHub repo

4. Select branch (e.g., `main`)

5. Set **Build Command**:

   ```
   pip install -r requirements.txt
   ```

6. Set **Start Command**:

   ```
   gunicorn app:app
   ```

7. Choose Python version (e.g., Python 3.10), and click **Deploy**

---

## Notes

* Uploaded resumes are stored in an `uploads/` folder. Ensure this is configured correctly for both local and production.
* If storing resumes on cloud (e.g., S3), update logic accordingly.
* Add authentication and database models for more advanced features.

---

##License

This project is open source and free to use under the [MIT License](LICENSE).

---

## Author

Built by SOBANA.RS
For any queries, feel free to open an issue or contact via GitHub.
