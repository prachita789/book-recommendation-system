from flask import Blueprint, render_template, session, redirect, url_for

recommendations = Blueprint('recommendations', __name__)

@recommendations.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template('dashboard.html')