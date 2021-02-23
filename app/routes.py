from flask import render_template, url_for, flash, redirect, request
from app import app, db, bcrypt, mail
from app.forms import RegistrationForm, LoginForm, RequestResetForm, ResetPasswordForm, AddToDoForm, ManageToDoForm
from app.models import User, ToDO
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message


@app.route("/", methods=['GET', 'POST'])
@app.route("/home", methods=['GET', 'POST'])
def home():
    if current_user.is_authenticated:
        if request.method == 'POST':
            if request.form.get('addTask') == 'Add Task':
                return redirect(url_for('add_task'))
            elif request.form.get('sortTask') == 'Sort by date':
                form2 = ManageToDoForm()
                todos_ordered = ToDO.query.filter_by(author=current_user).order_by(ToDO.due_date.asc())
                return render_template('home.html', todos=todos_ordered, form=form2)
        form = ManageToDoForm()
        todos = ToDO.query.filter_by(author=current_user)
        return render_template('home.html', todos=todos, form=form)
    return redirect(url_for('login'))


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Your account has been created! You are now able to log in!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request', sender='noreply@demo.com', recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)

@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)

@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash(f'Your password has been updated! You are now able to log in!', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)

@app.route("/add_task", methods=['GET', 'POST'])
@login_required
def add_task():
    form = AddToDoForm()
    if form.validate_on_submit():
        todo = ToDO(task=form.task.data, due_date=form.due_date.data, complete=False, author=current_user)
        db.session.add(todo)
        db.session.commit()
        flash('Task Added!', 'success')
        return redirect(url_for('home'))
    return render_template('add_task.html', title='Add Task', form=form, legend='Add Task')

@app.route("/edit_task/<int:todo_id>", methods=['GET', 'POST'])
@login_required
def edit_task(todo_id):
    todo = ToDO.query.get_or_404(todo_id)
    if todo.author != current_user:
        abort(403)
    form = AddToDoForm()
    if form.validate_on_submit():
        todo.task = form.task.data
        todo.due_date = form.due_date.data
        db.session.commit()
        flash('Your task has been updated!', 'success')
        return redirect(url_for('home'))
    elif request.method == 'GET':
        form.task.data = todo.task
        form.due_date.data = todo.due_date
    return render_template('add_task.html', title='Edit Task', form=form, legend='Edit Task')

@app.route("/delete_task/<int:todo_id>", methods=['GET', 'POST'])
@login_required
def delete_task(todo_id):
    todo = ToDO.query.get_or_404(todo_id)
    if todo.author != current_user:
        abort(403)
    db.session.delete(todo)
    db.session.commit()
    flash('Your task has been deleted!', 'success')
    return redirect(url_for('home'))

@app.route('/toggle_status/<int:todo_id>')
def toggle_status(todo_id):
    todo = ToDO.query.get(todo_id)
    todo.complete = not todo.complete
    db.session.commit()
    return redirect('/')