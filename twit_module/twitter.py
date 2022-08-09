from os import getenv
import tweepy
import pickle, spacy
from .models import DB, User, Tweet


key = getenv('TWITTER_API_KEY')
secret = getenv('TWITTER_API_KEY_SECRET')

TWITTER_AUTH = tweepy.OAuthHandler(key, secret)
TWITTER = tweepy.API(TWITTER_AUTH)


def add_or_update_user(username):
    '''
    add a twitter user by username, or update tweets if they are
    already in the database
    '''

    try:
        twitter_user = TWITTER.get_user(screen_name = username)

        db_user = (User.query.get(twitter_user.id) or User(
            id = twitter_user.id, username = username))
            
        tweets = twitter_user.timeline(
            count = 200,
            exclude_replies = True,
            include_rts = False,
            tweet_mode = 'extended',
            since_id = db_user.newest_tweet_id
            )

        if tweets:
            db_user.newest_tweet_id = tweets[0].id

        for tweet in tweets:
            tweet_vector = vectorize_tweet(tweet.full_text)
            db_tweet = Tweet(
                id = tweet.id,
                text = tweet.full_text[:300],
                vect = tweet_vector)
            db_user.tweets.append(db_tweet)
            DB.session.add(db_tweet)
    except Exception as e:
        print(f'Error: {e}')
        raise e
    else:
        DB.session.commit()

nlp = pickle.load(
    open('spacy_en_md.pkl', 'rb')
    )

def vectorize_tweet(tweet_text):
    return nlp(tweet_text).vector
