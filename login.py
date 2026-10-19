
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

login_dp = Blueprint("login", __name__)


class Login(db.Model):
    __tablename__ = "login"

    ID = db.Column(db.Integer, primary_key=True)
    FullName = db.Column(db.String(200), nullable=False, default="")
    Email = db.Column(db.String(254), unique=True, nullable=False)
    Username = db.Column(db.String(200), unique=True, nullable=False)
    Password = db.Column(db.String(500), nullable=False)


@login_dp.route("/register", methods=["GET", "POST"])
def register():
    # Already logged in → go to todos
    if "user_id" in session:
        return redirect(url_for("todos"))

    if request.method == "POST":
        fullname = request.form.get("fullname", "").strip()
        email = request.form.get("email", "").strip().lower()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirmPassword", "")

        if not all([fullname, email, username, password, confirm_password]):
            flash("Please fill in all fields.", "error")
            return redirect(url_for("login.register"))

        if len(username) < 3:
            flash("Username must contain at least 3 characters.", "error")
            return redirect(url_for("login.register"))

        if len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")
            return redirect(url_for("login.register"))

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("login.register"))

        existing_user = Login.query.filter(
            (Login.Username == username) | (Login.Email == email)
        ).first()

        if existing_user:
            flash("That username or email is already registered.", "error")
            return redirect(url_for("login.register"))

        user = Login(
            FullName=fullname,
            Email=email,
            Username=username,
            Password=generate_password_hash(password)
        )

        db.session.add(user)

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("Registration failed. Please try again.", "error")
            return redirect(url_for("login.register"))

        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("login.login"))

    return render_template("register.html")


@login_dp.route("/login", methods=["GET", "POST"])
def login():
    # Already logged in → go to todos
    if "user_id" in session:
        return redirect(url_for("todos"))

    if request.method == "POST":
        # Accept both 'Username' and 'username' from form
        username = (request.form.get("Username") or request.form.get("username") or "").strip()
        # Accept both 'Password' and 'password' from form
        password = (request.form.get("Password") or request.form.get("password") or "")

        user = Login.query.filter_by(Username=username).first()

        if user and check_password_hash(user.Password, password):
            session.clear()
            session["user_id"] = user.ID
            session["username"] = user.Username
            session["full_name"] = user.FullName
            flash(f"Welcome back, {user.FullName or user.Username}!", "success")
            return redirect(url_for("todos"))

        flash("Invalid username or password.", "error")
        return redirect(url_for("login.login"))

    return render_template("login.html")


@login_dp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for("home"))
