
# 📚 Advanced Library Management System (Flask + MySQL + Chatbot)

A complete Library Management System built with **Flask**, featuring Admin/Teacher/Student roles, SQLAlchemy models, Flask-Migrate support, and a smart Chatbot that answers natural language queries.

---

## 1️⃣ Create Virtual Environment

### **Windows**

```powershell
python -m venv venv
.\venv\Scripts\activate
```

### **Mac/Linux**

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 2️⃣ Install Dependencies

```
pip install -r requirements.txt
```

---

## 3️⃣ Create MySQL Database

Login to MySQL:

```bash
mysql -u root -p
```

Create the database:

```sql
CREATE DATABASE library_db;
```

---

## 4️⃣ Configure Database in config.py

Open **config.py** and update:

```python
DATABASE_URL = "mysql+pymysql://root:YOURPASSWORD@localhost/library_db"
SECRET_KEY = "yoursecretkey"
```

Replace:

* `YOURPASSWORD` → your MySQL root password
* `yoursecretkey` → any random secret key

---

## 5️⃣ Initialize Database (Flask-Migrate)

First, set the Flask application:

### **Windows PowerShell**

```powershell
$env:FLASK_APP="manage.py"
```

### **Mac/Linux**

```bash
export FLASK_APP=manage.py
```

Now run:

```bash
flask db init
flask db migrate -m "initial"
flask db upgrade
```

This will create all required tables:

* users
* books
* borrow_records
* book_recommendations

---

