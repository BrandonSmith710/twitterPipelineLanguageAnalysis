from flask import Flask, render_template, request
from .twitter import add_or_update_user
from .models import DB, User, UserIP, Tweet
from .predict import predict_user, topicizer
from .db_ip import *
from os import getenv

def create_app():

    app = Flask(__name__)

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///twitterusers.db'
    pg_conn = connect_pg(
        dbname = getenv('DB_NAME'),
        user = getenv('USER'),
        password = getenv('PASSWD'),
        host = getenv('HOST')
        )
    pg_curs = get_curs(pg_conn)
    init_ip_table(pg_curs, pg_conn)
    DB.init_app(app)

    @app.before_first_request
    def create_tables():
        DB.create_all()

    @app.route('/')
    def root():
        title = 'View who is more likely to have tweeted it'
        return render_template('home.html', title = title, users = User.query.all())

    @app.route('/update')
    def update():
        # update users with their latest tweets

        users = User.query.all()
        usernames = [user.username for user in users]
        for username in usernames:
            add_or_update_user(username)
        return render_template('home.html',
            title = "All users have been updated to include their latest tweets.")
    
    @app.route('/reset')
    def reset():
        # empty all tables in the database

        DB.drop_all()
        DB.create_all()
        return 'Database has been cleared'

    @app.route('/user', methods = ['POST'])
    @app.route('/user/<name>', methods = ['GET'])
    def user(name = None, message = ''):
        # add a user to the database, display their recent tweets

        name = name or request.values['user_name']
        try:
            if request.method == 'POST':
                add_or_update_user(name)
                message = f'User "{name}" was successfully added.'
            tweets = User.query.filter(User.username == name).one().tweets
            insert_ip(pg_curs, pg_conn, request.remote_addr)
        except Exception as e:
            message = f'Error adding {name}: {e}'
            tweets = []
        else:
            return render_template('user.html', title = name, tweets = tweets,
                                                              message = message)

    @app.route('/topic', methods = ['POST'])
    def topic():
        '''
        generate a list the topics discussed in a specified
        twitter user's recent tweets
        '''     

        user = request.values['user']
        tweets = User.query.filter(User.username == user).one().tweets
        topics = topicizer([tweet.text for tweet in tweets])
        insert_ip(pg_curs, pg_conn, request.remote_addr)
           
        return render_template('topics.html', title = 'Topics', message = topics)

    @app.route('/predict_author', methods = ['POST'])
    def predict_author():
        '''
        select two existing users from dropdown menu, enter a hypothetical tweet,
        and view the logistic regression prediction of which user is more likely
        to have tweeted it
        '''
        
        user0, user1 = sorted([request.values[x] for x in ['user0', 'user1']])

        if user0 == user1:
            message = 'Cannot compare a user to themselves!'
        else: 
            tweet_text = request.values['tweet_text']
            prediction = predict_user(user0, user1, tweet_text)
            message = '''"{}" is more likely to be said 
                         by {} than {}.'''.format(tweet_text, 
                                                  user1 if prediction else user0, 
                                                  user0 if prediction else user1)
        insert_ip(pg_curs, pg_conn, request.remote_addr)
        return render_template('prediction.html', title = 'Prediction', message = message)

    @app.route('/_see_addresses', methods = ['GET', 'POST'])
    def _see_addresses():
        if request.method == 'POST':
            passwd = request.values['admin_pass']
            admin_passwd = getenv('ADMIN_PASS')
            if admin_passwd == passwd:
                return get_ips(pg_curs)
            return 'INVALID PASSWORD'
        return render_template('_see_addresses.html')

    return app
