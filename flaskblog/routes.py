import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from flaskblog import app, db, bcrypt
from flaskblog.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm
from flaskblog.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required

@app.route("/")
@app.route("/home")
def home():
    posts = Post.query.all() #Grab all posts from database
    return render_template('home.html', posts=posts)


@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash('Your accound has been created! You are now able to log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: #If user is logged in already
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first() #Check if database has email
        if user and bcrypt.check_password_hash(user.password, form.password.data): #makes sure user exists and has correct password
            login_user(user, remember=form.remember.data) #Logs in user
            next_page = request.args.get('next') #If user tries to access login page, and we want to redirect them there as soon as they log in

            return redirect(next_page) if next_page else redirect(url_for('home')) #redirect user to home if no next_page in url
        else: #Unsuccessful login
            flash('Login Unsuccessful. Please check email and password', 'danger') #If we don't hit conditional,
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext 
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    #Resize
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)

    i.save(picture_path) #i is the new image from the form_picture
    return picture_fn

@app.route("/account", methods=['GET', 'POST'])
@login_required # We need to login to access this route
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data: # Handling changing picture logic
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email

    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account', image_file=image_file, form=form)


@app.route("/post/new", methods=['GET', 'POST'])
@login_required #need to be logged in
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post) #Adds post to database
        db.session.commit() #Commits the post
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post', 
                            form=form, legend='NewPost')

@app.route("/post/<int:post_id>") #postid=1 if post/1, etc
def post(post_id):
    post = Post.query.get_or_404(post_id) # If it doesn't exist, return 404, but if it exists, render a template
    return render_template('post.html', title=post.title, post=post)

@app.route("/post/<int:post_id>/update", methods=['GET', 'POST']) #postid=1 if post/1, etc
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id) # If it doesn't exist, return 404, but if it exists, render a template
    if post.author != current_user:
        abort(403) #Return 403 which is http response for forbidden route
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit() #Don't need to add because they're in the database
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title #The form's title will be the post.title - confused
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post', 
                            form=form, legend='UpdatePost')


@app.route("/post/<int:post_id>/delete", methods=['POST']) #postid=1 if post/1, etc
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id) # If it doesn't exist, return 404, but if it exists, render a template
    if post.author != current_user:
        abort(403) #Return 403 which is http response for forbidden route
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))
