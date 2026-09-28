import os
from flask import Flask, render_template, request , redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

os.makedirs('instance', exist_ok=True)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "instance", "todo.db")}'
db = SQLAlchemy(app)

class ToDo(db.Model):
    SNo = db.Column(db.Integer, primary_key=True)
    TODO_Title = db.Column(db.String(200), nullable=False)
    Description = db.Column(db.String(500), nullable=False)
    Date_Time = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"{self.SNo} - {self.TODO_Title}"

@app.route('/', methods=['GET', 'POST'])
def welcome():
    if request.method == "POST":
        title = request.form.get('todoTitle') 
        description = request.form.get('todoDescription')  
        
        if title and description:
            todo = ToDo(TODO_Title=title, Description=description)
            db.session.add(todo)
            db.session.commit()
            print(f"Added TODO: {title}")
    
    # ✅ ONLY FETCH TODOS, DON'T CREATE NEW ONES
    allTODO = ToDo.query.all()
    return render_template('index.html', allTODO=allTODO)

@app.route('/home')
def home():
    return 'WELCOME TO THE HOME PAGE OF TODO APP'

@app.route('/show')
def show():
    allTODO = ToDo.query.all()
    return render_template('index.html', allTODO=allTODO)
    
@app.route('/update/<int:SNo>', methods=['GET', 'POST'])
def update(SNo):
    todo = ToDo.query.get(SNo)  # Get the specific todo to update
    
    if not todo:
        return redirect('/')
    
    if request.method == "POST":
        todo.TODO_Title = request.form.get('todoTitle')
        todo.Description = request.form.get('todoDescription')
        db.session.commit()
        return redirect('/')
    
    # GET request - show the update form
    allTODO = ToDo.query.all()  # Just .all() - no .first()
    return render_template('update.html', allTODO=allTODO, edit_todo=todo)
    
@app.route('/delete/<int:SNo>')
def delete(SNo):
    todo = ToDo.query.get(SNo)  # Cleaner for primary key lookups
    
    if todo:
        db.session.delete(todo)
        db.session.commit()
        print(f"Deleted TODO: {todo.TODO_Title}")
    
    return redirect('/')
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
