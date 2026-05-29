from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

auth = Blueprint('auth', __name__)


#

@auth.route('/register', methods=['GET', 'POST'])
def register():

    from extensions import mysql

    # Prevent logged-in users from opening register page
    if session.get('user_id'):
        return redirect(url_for('recommendations.dashboard'))

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        hashed_password = generate_password_hash(password)

        try:

            cur = mysql.connection.cursor()

            # Insert user
            cur.execute("""
                INSERT INTO users
                (name, email, password)
                VALUES (%s, %s, %s)
            """, (name, email, hashed_password))

            mysql.connection.commit()

            # Fetch newly created user
            cur.execute("""
                SELECT *
                FROM users
                WHERE email = %s
            """, (email,))

            new_user = cur.fetchone()

            cur.close()

            # Auto login
            session['user_id'] = new_user['id']
            session['user_name'] = new_user['name']
            session['user_email'] = new_user['email']

            flash(f"Welcome {new_user['name']}!", 'success')

            return redirect(url_for('onboarding.onboarding'))

        except Exception as e:

            print("REGISTER ERROR:", str(e))

            flash('Email already exists. Try another.', 'danger')

            return redirect(url_for('auth.register'))

    return render_template('register.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    from app import mysql
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            cur = mysql.connection.cursor()
            cur.execute(
                "SELECT * FROM users WHERE email = %s", (email,)
            )
            user = cur.fetchone()
            cur.close()

            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['user_name'] = user['name']
                session['user_email'] = user['email']
                flash(f"Welcome back {user['name']}!", 'success')
                return redirect(url_for('recommendations.dashboard'))
            else:
                flash('Invalid email or password!', 'danger')
                return redirect(url_for('auth.login'))

        except Exception as e:
            print("ERROR:", str(e))
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('auth.login'))

    return render_template('login.html')

@auth.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('books.home'))



