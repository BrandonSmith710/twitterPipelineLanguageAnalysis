from flask import Flask, render_template, request
from .twitter import add_or_update_user
from .models import DB, User, Tweet
from .predict import predict_user

def create_app():

    app = Flask(__name__)

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///twitterusers.db'
    
    DB.init_app(app)

    @app.before_first_request
    def create_tables():
        DB.create_all()

    @app.route('/')
    def root():
        return render_template('home.html', title = 'Home', users = User.query.all())

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
        except Exception as e:
            message = f'Error adding {name}: {e}'
            tweets = []
        else:
            return render_template('user.html', title = name, tweets = tweets,
                                                              message = message)

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
        return render_template('prediction.html', title = 'Prediction', message = message)

    return app