class Config:
    SECRET_KEY = 'your-secret-key'   # You can replace with a random key later
    SQLALCHEMY_DATABASE_URI = 'sqlite:///record.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_TYPE = 'filesystem'
