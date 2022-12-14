from flask_sqlalchemy import SQLAlchemy

DB = SQLAlchemy()

class User(DB.Model):
    id = DB.Column(DB.BigInteger, primary_key = True, nullable = False)

    username = DB.Column(DB.String, nullable = False)

    newest_tweet_id = DB.Column(DB.BigInteger)

    def __repr__(self):
        return f'<User: {self.username}>'

class Tweet(DB.Model):

    id = DB.Column(DB.BigInteger, primary_key = True, nullable = False)

    text = DB.Column(DB.Unicode(300), nullable = False)

    vect = DB.Column(DB.PickleType, nullable = False)

    user_id = DB.Column(DB.BigInteger, DB.ForeignKey('user.id'), nullable = False)

    user = DB.relationship('User', backref = DB.backref('tweets'), lazy = True)

    def __repr__(self):
        return f'<Tweet: {self.text}>'

class UserIP(DB.Model):
    ip = DB.Column(DB.String(50), primary_key = True, nullable = False)
