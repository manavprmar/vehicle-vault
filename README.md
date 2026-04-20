# 🚗 Vehicle Vault

**Vehicle Vault** is a Django-based web application that allows users to **buy, sell, and manage vehicles online**.
It provides features for vehicle listings, user authentication, inspection requests, messaging, and secure transactions.

## 🛠 Tech Stack

![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![HTML](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![CSS](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![Git](https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=git&logoColor=white)
![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)

# 📌 Features

### 👤 User Management

* Custom User Model
* Buyer and Seller roles
* Secure authentication system

### 🚘 Vehicle Listings

* Add and manage car listings
* Upload multiple car images
* View detailed vehicle information

### 🔍 Search & Browse

* Browse all available vehicles
* Filter by brand or category
* View featured listings

### 💬 Messaging System

* Buyers can contact sellers
* Communication inside the platform

### 🧾 Test Drive & Inspection

* Request vehicle test drives
* Inspection management

### 💳 Transaction Management

* Manage vehicle purchase transactions
* Track order status

---

# 🛠️ Tech Stack

| Technology     | Usage             |
| -------------- | ----------------- |
| **Django**     | Backend framework |
| **PostgreSQL** | Database          |
| **HTML/CSS**   | Frontend          |
| **JavaScript** | UI interactions   |
| **Bootstrap**  | Responsive design |

---

# 📂 Project Structure

```
Vehicle-Vault
│
├── cars/
│   ├── migrations/
│   ├── templates/
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   └── urls.py
│
├── vehiclevault/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── static/
├── media/
├── manage.py
└── README.md
```

---

# ⚙️ Installation Guide

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/yourusername/Vehicle-Vault.git
cd Vehicle-Vault
```

---

### 2️⃣ Create Virtual Environment

**Windows**

```bash
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux**

```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 3️⃣ Install Dependencies

```bash
pip install django psycopg2-binary
```

---

### 4️⃣ Configure Database

Update your **settings.py**

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'vehiclevault',
        'USER': 'postgres',
        'PASSWORD': 'yourpassword',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

Create database:

```sql
CREATE DATABASE vehiclevault;
```

---

### 5️⃣ Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

---

### 6️⃣ Create Superuser

```bash
python manage.py createsuperuser
```

---

### 7️⃣ Run Server

```bash
python manage.py runserver
```

Open in browser:

```
http://127.0.0.1:8000
```

Admin panel:

```
http://127.0.0.1:8000/admin
```

---

# ⚠️ Common Error Fix

### ❌ Error

```
django.db.utils.ProgrammingError:
column cars_user.vault_code does not exist
```

### ✅ Solution

Run migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

This will update the database with the **vault_code** field.

---

# 🧪 Running Tests

```bash
python manage.py test
```

---

# 🚀 Deployment

For production deployment use:

* **Gunicorn**
* **Nginx**
* **PostgreSQL**

Run:

```bash
python manage.py collectstatic
```

# 🤝 Contributing

Contributions are welcome!

Steps:

1. Fork the repository
2. Create a new branch
3. Commit changes
4. Push to GitHub
5. Open a Pull Request

# 📜 License

This project is licensed under the **MIT License**.

# 👨‍💻 Author

Developed by **Vehicle Vault Team**

