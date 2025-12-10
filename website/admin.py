from flask import Blueprint, render_template, request, redirect, url_for, flash
from .models import Signupuser,BarPlot
from flask_login import current_user,login_required
from . import db

admin_bp = Blueprint('admin', __name__)
@admin_bp.route('/admin', methods=['POST', 'GET'])
def admin_dashboard():
    login_required
    if current_user.id==5:
        users = Signupuser.query.all()
        return render_template('admin_dashboard.html', users=users)
    return render_template("404.html")
    
@admin_bp.route('/delete-user/<int:id>')
def delete_user(id):
    try:
        # Step 1: Manually delete all BarPlot records for this user
        db.session.query(BarPlot).filter_by(user_id=id).delete()
        db.session.commit()  # Ensure BarPlots are deleted first

        # Step 2: Now delete the user
        user = Signupuser.query.get(id)
        if user:
            db.session.delete(user)
            db.session.commit()
            flash(f"User ID {id} and related BarPlot records deleted successfully.", "success")
        else:
            flash("User not found.", "danger")

    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting user: {str(e)}", "danger")

    return redirect(request.referrer or url_for('admin.dashboard'))
