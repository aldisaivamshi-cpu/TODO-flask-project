import os
from datetime import datetime
from zoneinfo import ZoneInfo
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from extensions import db
from login import login_dp, Login

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "change-this-secret-key-in-production")
instance_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "instance")
os.makedirs(instance_dir, exist_ok=True)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(instance_dir, "todo.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


def india_time():
    return datetime.now(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)


class ToDo(db.Model):
    __tablename__ = "todos"
    SNo = db.Column(db.Integer, primary_key=True)
    TODO_Title = db.Column(db.String(200), nullable=False)
    Description = db.Column(db.String(500), nullable=False)
    Date_Time = db.Column(db.DateTime, default=india_time)
    # Link each todo to its owner
    user_id = db.Column(db.Integer, db.ForeignKey("login.ID"), nullable=True)


app.register_blueprint(login_dp)

with app.app_context():
    db.create_all()


# ── Auth guard decorator ──────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access your TODOs.")
            return redirect(url_for("login.login"))
        return f(*args, **kwargs)
    return decorated


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def welcome():
    """Landing page — redirect logged-in users to their TODOs."""
    if "user_id" in session:
        return redirect(url_for("todos"))
    return redirect(url_for("home"))


@app.route("/home")
def home():
    return render_template("home.html")


@app.route("/todos", methods=["GET", "POST"])
@login_required
def todos():
    user_id = session["user_id"]

    if request.method == "POST":
        title = request.form.get("todoTitle", "").strip()
        description = request.form.get("todoDescription", "").strip()
        if title and description:
            db.session.add(ToDo(
                TODO_Title=title,
                Description=description,
                Date_Time=india_time(),
                user_id=user_id
            ))
            db.session.commit()
            flash("Task added successfully!", "success")
        else:
            flash("Title and description are required.", "error")
        return redirect(url_for("todos"))

    allTODO = ToDo.query.filter_by(user_id=user_id).order_by(ToDo.SNo.asc()).all()
    return render_template("index.html", allTODO=allTODO)


@app.route("/update/<int:SNo>", methods=["GET", "POST"])
@login_required
def update(SNo):
    user_id = session["user_id"]
    todo = db.session.get(ToDo, SNo)

    # Protect: users can only edit their own todos
    if todo is None or todo.user_id != user_id:
        flash("Task not found.", "error")
        return redirect(url_for("todos"))

    if request.method == "POST":
        title = request.form.get("todoTitle", "").strip()
        description = request.form.get("todoDescription", "").strip()
        if title and description:
            todo.TODO_Title = title
            todo.Description = description
            todo.Date_Time = india_time()
            db.session.commit()
            flash("Task updated successfully!", "success")
        return redirect(url_for("todos"))

    return render_template("update.html", edit_todo=todo)


@app.route("/delete/<int:SNo>")
@login_required
def delete(SNo):
    user_id = session["user_id"]
    todo = db.session.get(ToDo, SNo)

    if todo is not None and todo.user_id == user_id:
        db.session.delete(todo)
        db.session.commit()
        flash("Task deleted.", "success")
    return redirect(url_for("todos"))


@app.route("/about")
def about():
    return render_template("about.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
