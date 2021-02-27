from flask import Flask, render_template, request, session, redirect
import pymysql
from flask_sqlalchemy import SQLAlchemy                 # importing flask sqlAlchemy for connecting our flask backend to sql database.
from datetime import datetime
import json
from flask_mail import Mail                             # importing flask mail for sending email to website owner everytime anyone submit contact form
from flask_mail import Message                          # importing Message for sending email.
import os                                               # OS module for saving uploaded file
from werkzeug.utils import secure_filename  
import time 
import math                 


""" If it gives 'no module mysqldb() found then open cmd and 'pip install PyMySQL'
and add 'import pymysql' and 'pymysql.install_as_MySQLdb()' to your code. """

""" In cmd run 'pip install flask-sqlalchemy' first before doing anything.
Use this link to learn about how to setup sqlAlchemy: https://flask-sqlalchemy.palletsprojects.com/en/2.x/quickstart/
sample sqlAlchemy database URI: 'mysql://username:password@localhost/db_name'
here, change every portion of this according to your requirements.
"""


with open('config.json', 'r') as config_file:       # Opening config.json file and from here we will read all the parameters required.
    params = json.load(config_file)["params"]


local_server = True                                 # Making local server as true by default

app = Flask(__name__,template_folder='templates')
app.secret_key = "blog_testing key"
app.config['UPLOAD_FOLDER'] = params['upload_location']

app.config.update(          
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail_username'],
    MAIL_PASSWORD = params['gmail_password']
)                                               # Defining basic config for our SMTP
mail = Mail(app)                                # Creating an mail object and passing our flask app to it.

if (local_server):              # Stating whether to take local URI or production URI
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_URI']           # for referring to which database to connect. It will fetch from config.json
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['production_URI']


db = SQLAlchemy(app)                                                            # Initializing our db variable
pymysql.install_as_MySQLdb()


""" Now we make a class that will define our tables in database. As copied from sqlAlchemy quickstart guide. One class will define one table in database.
change its details according to your use."""
class Contact_info(db.Model):
    """ sno,name,email,phone,message,date_time """                  # Exact sequence of entries
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(25), nullable=False)
    phone = db.Column(db.String(14),  nullable=False)
    message = db.Column(db.String(120), nullable=False)
    date_time = db.Column(db.String(12), nullable = True)



@app.route("/")
def home():

    # pagination logic
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_post']))
    # [0:params['no_of_post']]
    page = request.args.get('page')                # getting what page number is it. Typecasting it into int so we can do addition/subtraction
    if (not str(page).isnumeric()):                     # saying if page no is not numeric, make it zero
        page = 1


    page = int(page)
    posts = posts[(page - 1)*int(params['no_of_post']): (page - 1)*int(params['no_of_post']) + int(params['no_of_post'])]           # this is post slicing

    # on first page
    if (page == 1):
        prev_page = "#"
        next_page = "/?page="  + str(page + 1)

    # on last page
    elif (page == last):
        next_page = "#"
        prev_page = "/?page="  + str(page - 1)

    # in middle pages
    else:
        next_page = "/?page="  + str(page + 1)
        prev_page = "/?page="  + str(page - 1)



    return render_template('index.html', params = params, posts = posts, prev_page = prev_page, next_page = next_page)


@app.route("/about")
def about():
    return render_template('about.html', params = params)

@app.route("/contact", methods = ['GET','POST'])
def contact():

    if (request.method == 'POST'):
        """ ADD ENTRY TO THE DB """
        name_form = request.form.get('name')                 # here we are fetching values entered in our form.
        email_form = request.form.get('email')
        phone_form = request.form.get('phone')
        message_form = request.form.get('message')

        """ sno,name,email,phone,message,date_time """  # Exact sequence of entries
        myDateTime = datetime.now()

        entry = Contact_info(name = name_form, email = email_form, phone = phone_form, message = message_form, date_time = myDateTime)          # Giving values collected from form to exact database columns
        db.session.add(entry)
        db.session.commit()


        """ After commiting addition in our DB we will send an email about it to the blog owner 
        use params in config.json file and add your gmail username and password in it first 
        
        Make sure to enable 'Less secure app access' in your gmail account. Here we will use google's SMTP server"""
        msg = Message("New Message from Blog by "+name_form+"<"+email_form+">",
                  sender=(name_form, email_form),
                  recipients=[params['gmail_username']],
                  body=message_form+"\nPhone Number: "+phone_form)
        
        mail.send(msg)          # Sending message

    return render_template('contact.html', params = params)





""" Just like we made a class to fetch/post entries in contact table, we also need a class for posts. """
class Posts(db.Model):
    """ sno, title, subtitle, slug, content, img_file, date """                  # Exact sequence of entries
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    subtitle = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(30), nullable=False)
    content = db.Column(db.String(120),  nullable=False)
    img_file = db.Column(db.String(20), nullable = False)
    date = db.Column(db.String(12), nullable=False)






""" Now we will fetch and display our post from database. """
              

@app.route("/post/<string:post_slug>", methods=['GET'])                      # this app.route gives post route according to unique slug. And only GET method is used.
def post_route(post_slug):

    
    post = Posts.query.filter_by(slug=post_slug).first()                     # This line will querry within the post table by slug.
    return render_template('post.html', params=params, post=post)            # This way we are passing our params to every page, also passing our fetched post.



""" Now we will make a dashboard for admin to upload new blogs. We have already made a log_in.html file from bootstrap. """

@app.route("/dashboard", methods = ['GET','POST'])
def dashboard():


    if 'username' in session:                # it will check whether the user is already is in session. if yes then no need to show him login form and directly send him dashboard page.
        username = session['username']
        posts = Posts.query.all()
        return render_template('dashboard.html', params = params, posts = posts)


    if(request.method == 'POST'):

        
        username_entered = request.form.get('username')
        pass_entered = request.form.get('password')

        if(username_entered == params['admin_username'] and pass_entered == params['admin_password']):
            #set the session variable
            session['username'] = params['admin_username']


            posts = Posts.query.all()
            return render_template('dashboard.html', params = params, posts = posts)
            
            #redirect to admin pannel
        else:      
            wrong_credentials = 1
            return render_template('log_in.html', wrong_credentials = wrong_credentials, params = params)
            


    else:
        return render_template('log_in.html', params = params)



@app.route("/logout")
def logout():  
    session.pop('username') 
    return redirect("/dashboard")



""" Now we are creating a route to edit our post within from dashboard. 
if html comes with edit/0 then new post is created but else it will edit with same post number and we are fetching the data from db to make it editable."""

@app.route("/edit/<string:sno>", methods = ['GET','POST'])
def edit(sno):
     if 'username' in session:

        if request.method == 'POST':                    # only works when submit button is clicked
            box_title = request.form.get('title')
            box_subtitle = request.form.get('subtitle')
            box_slug = request.form.get('slug')
            box_content = request.form.get('content')
            box_img_file = request.form.get('img_file')
            date_now = datetime.now()

            if sno == '0':                              # creating new post
                post = Posts(title = box_title, subtitle = box_subtitle, slug = box_slug, content = box_content, img_file = box_img_file, date = date_now)
                db.session.add(post)
                db.session.commit()
                return redirect("/dashboard")

            else:                                       # fetching post from db using sno and editing it, and when submit is clicked then same changes is made in db.
                post = Posts.query.filter_by(sno = sno).first()
                post.title = box_title
                post.subtitle = box_subtitle
                post.slug = box_slug
                post.content = box_content
                post.img_file = box_img_file
                db.session.commit()
                return redirect('/edit/' + sno)         # using redirect module from flask, after changes made it will redirect to same edit page.


        post = Posts.query.filter_by(sno = sno).first()             # for when request method is not post. just for showing edit.html, when  sno is 0 then it can't find anything in db but if we are editing and got here by redirect it will show querry according to sno.
        return render_template('edit.html', params = params, post = post, sno = sno)



""" Now we will create an uploader. """

@app.route("/uploader", methods = ['GET','POST'])
def uploader():
    if 'username' in session:
        if request.method == 'POST':
            f = request.files('file1')
            filename = secure_filename(f.filename)
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return "Uploaded Successfully"



@app.route("/delete/<string:sno>")
def delete(sno):
    if 'username' in session:
        post = Posts.query.filter_by(sno = sno).first()
        db.session.delete(post)
        db.session.commit()
        return redirect("/dashboard")


app.run(debug = True)