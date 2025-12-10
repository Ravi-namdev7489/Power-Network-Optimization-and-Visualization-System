from . import db
from flask_login import UserMixin
from sqlalchemy.dialects.mysql import LONGTEXT
from datetime import datetime
import pytz

# Helper: Current time in India
def current_time_india():
    india = pytz.timezone("Asia/Kolkata")
    return datetime.now(india)

# Signupuser Model
class Signupuser(UserMixin, db.Model):
    __tablename__ = 'signupuser'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(300), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)

    # Relationship to BarPlot with cascade delete
    bar_plots = db.relationship(
        'BarPlot',
        backref='user',
        cascade='all, delete-orphan',
        passive_deletes=True
    )

# BarPlot Model
class BarPlot(db.Model):
    __tablename__ = 'bar_plot'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('signupuser.id', ondelete='CASCADE'),
        nullable=False
    )
    result_type = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=current_time_india, nullable=False)
    input_params = db.Column(db.Text, nullable=True)
    output_params = db.Column(db.Text, nullable=True)
    plot_data = db.Column(db.Text)   # Store plot HTML or JSON
