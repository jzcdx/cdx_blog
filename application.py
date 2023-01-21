from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from datetime import datetime
import os
import sqlite3
from sqlite3 import IntegrityError
import secrets

basedir = os.path.abspath(os.path.dirname(__file__))

application = Flask(__name__)
application.config['SQLALCHEMY_DATABASE_URI']="sqlite:///"+os.path.join(basedir, "instance/posts.db")
application.secret_key = secrets.token_urlsafe(16)
    
with application.app_context():
    db = SQLAlchemy(application)


class Article(db.Model):
    id = db.Column(db.Integer, primary_key = True)

    title = db.Column(db.String(200), unique=True)
    content = db.Column(db.String(5000), nullable=False) #5000 character limit for now
    tags = db.Column(db.String(500), nullable=False) #gonna make this comma separated lol
    date_created = db.Column(db.DateTime, default=datetime.utcnow) 

    def __repr__(self):
        return '<Task %r>' % self.id

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return '<Task %r>' % self.id

@application.route("/")
def main():
    #session['logged_in'] = False
    articles = Article.query.order_by(Article.date_created.desc()).all()
    return render_template("index.html", articles=articles, session=session)

@application.route("/new_article.html", methods=['GET', 'POST'])
def add_new_article():
    if request.method == 'POST':
        new_article = Article(title=request.form['title_form'], content=request.form['content_form'], tags=request.form['tag_form'])
        try:
            db.session.add(new_article)
            db.session.commit()
            return redirect("/") #leads you back to index after
        except sqlite3.IntegrityError as ex:
            return 'Article title already taken'
        except Exception as ex:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            return 'Error adding new article'
    else:
        if session.get('logged_in') == True:
            return render_template("new_article.html")
        else:
            return redirect("/login.html")

@application.route("/delete/<int:id>") #<int:id> id is the variable name that we're passing from our html, must be in the method parameters as well
def delete(id):
    if session.get('logged_in') == True:
        delete_me = Article.query.get_or_404(id)
        try:
            db.session.delete(delete_me)
            db.session.commit()
        except:
            return 'unknown error'
        return redirect("/")
    else:
        return redirect("/login.html")

@application.route("/edit/<int:id>", methods=['POST', 'GET'])
def edit(id):
    article_to_edit = Article.query.get_or_404(id)
    if request.method == "POST":
        article_to_edit.title = request.form['title_form']
        article_to_edit.content = request.form['content_form']
        article_to_edit.tags = request.form['tag_form']
        
        try:
            db.session.commit()
            return redirect("/")
        except:
            return 'Error editing article'
    else:
        if session.get('logged_in') == True:
            return render_template("edit.html", article=article_to_edit)
        else:
            return redirect("/login.html")
@application.route("/login.html", methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        username_input = request.form["username_input"]
        password_input = request.form["password_input"]
        print(username_input, password_input)
        user = User.query.filter_by(username=username_input).first()

        if user: #aka there is a user with that username
            if user.password == password_input:
                application.secret_key = secrets.token_urlsafe(16) #so this resets the session
                session["logged_in"] = True
                session["username"] = user.username
                session["user_id"] = user.id
                print("logged in: " , session["username"])#
                return redirect("/")
            else:
                return render_template("login.html")
        else: #if username doesn't exist
            return render_template("login.html")
    else: #first visit, no request
        return render_template("login.html")

@application.route('/logout')
def logout():
    session.clear()
    application.secret_key = secrets.token_urlsafe(16) #so this resets the session
    return redirect("/")

if __name__ == "__main__":
    application.run(debug=True, use_reloader=False)