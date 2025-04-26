⌚ Watch Haven (Flask Project)

Watch Haven is a full-stack Flask web application for selling luxury watches online.
It provides user authentication, watch browsing, shopping cart, checkout system, and an admin panel for managing orders and watches.

🛠 Tech Stack
Backend Framework: Flask (Python)

Frontend Templating: Jinja2 (HTML Templates)

Database: SQLite (watches.db)

ORM: Flask-SQLAlchemy

Forms: Flask-WTF

Authentication: Flask-Login

Styling: Custom CSS

Assets: Static images and video support

📦 Features
User Authentication: Registration, login, logout

Product Catalog: Browse and view watch details

Search Functionality: Search watches by keyword

Shopping Cart: Add to cart, remove from cart

Order System: Place orders and view past orders

Admin Dashboard:

Add/Edit/Delete Watches

Manage Orders

Responsive Layout: Mobile and desktop friendly

Media: Banner images, product images, and promotional videos

📁 Project Structure

Final Project/
│
├── app.py            # Main Flask app
├── forms.py          # WTForms classes
├── models.py         # Database models
├── routes.py         # All route definitions
├── instance/
│   └── watches.db    # SQLite Database
├── static/
│   ├── css/style.css
│   ├── images/
│   └── videos/
├── templates/
│   ├── (User Pages)
│   └── admin/
├── __pycache__/
🚀 How to Run

# 1. Clone the repository
git clone https://github.com/your-username/watch_haven.git
cd "Final Project"

# 2. Install dependencies
pip install flask flask_sqlalchemy flask_wtf flask_login

# 3. Run the app
python app.py
Server will run on http://127.0.0.1:5000/

📸 Screenshots
![image](https://github.com/user-attachments/assets/f3c40371-2f82-4087-9af3-161d752e16dc)


📜 License
This project is for educational purposes only.


