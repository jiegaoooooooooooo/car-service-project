content = """# 🚗 Apple Garage - Full-Stack Car Service & Garage Management System

[![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-Web%20Framework-green.svg)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey.svg)](https://www.sqlite.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-4.5-purple.svg)](https://getbootstrap.com/)

A comprehensive, role-based full-stack web application designed to digitize and streamline car garage operations, appointment booking, and vehicle maintenance tracking. 

---

## 🌟 Features & Role-Based Access Control

The system supports three distinct user roles with tailored functionalities:

### 1. 👤 Customer Portal
* **Smart Vehicle Registration**: Automatically fetches vehicle specifications (MOT status, tax, make, engine capacity, etc.) via the **UK Government DVLA REST API** using just the registration number.
* **Online Booking**: Schedule maintenance services (MOT, Full Service, Oil Change, Brakes, etc.), choose dates, and attach custom notes.
* **Maintenance History**: Track past and upcoming services, check real-time repair statuses, and cancel scheduled bookings.

### 2. 🔧 Staff Portal
* **Automated Check-in**: Daily attendance tracking upon staff login.
* **Job Management**: View available jobs, pick tasks, assign collaborating mechanics, and update job statuses (*Working, Paused, Completed*).
* **Technical Assistance**: 
  * Look up car part product codes and reference history.
  * View historical problem logs for specific vehicle models to troubleshoot faster.

### 3. 📊 Manager Dashboard
* **Color-Coded Master Service Record**: Instantly track shop-wide job progress using dynamic status color-coding (Scheduled, Working, Paused, Done, Paid).
* **Financial Management**: Input total service charges to finalize and close out completed jobs.
* **Administrative Control**: Create new staff accounts and manage overall garage workflow.

---

## 🛠️ Tech Stack

* **Backend**: Python, Flask, SQLite, `sqlite3`, `bcrypt` (secure password hashing & salting), `requests` (API integration).
* **Frontend**: HTML5, CSS3, JavaScript (ES6+), Bootstrap 4.5, Jinja2 templating.
* **External API**: UK Government Vehicle Enquiry Service (VES) API.

---

## 📸 Demo

```markdown
![Apple Garage Demo](preview.gif)
