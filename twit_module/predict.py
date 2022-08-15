import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import TfidfVectorizer
import re
from .models import User
from .twitter import vectorize_tweet

def predict_user(user0_username, user1_username, hypo_tweet_text):
    '''
    Determine and returns which user is more likely to say a given tweet
    Example run: predict_user("elonmusk", "jackblack", "Tesla cars go vroom")
    Returns a 0 (user0_name: "elonmusk") or a 1 (user1_name: "jackblack")
    '''

    user0 = User.query.filter(User.username == user0_username).one()
    user1 = User.query.filter(User.username == user1_username).one()

    # Get a list of word embeddings for each user's tweets
    user0_vects = np.array([tweet.vect for tweet in user0.tweets])
    user1_vects = np.array([tweet.vect for tweet in user1.tweets])
    
    # combine the user's tweet's word embeddings into one np array
    # X Matrix for training
    vects = np.vstack([user0_vects, user1_vects])

    # combine labels into one array
    zeros = np.zeros(len(user0.tweets))
    ones = np.ones(len(user1.tweets))
    # y vector for training
    labels = np.concatenate([zeros, ones])

    log_reg = LogisticRegression()
    log_reg.fit(vects, labels)

    # Generate a prediction for our hypothetical tweet text
    hypo_tweet_vect = vectorize_tweet(hypo_tweet_text)

    # pass in 2D array to the regression model
    prediction = log_reg.predict([hypo_tweet_vect])

    return prediction[0]


tfidf_vect = TfidfVectorizer(max_df=.8, stop_words='english')

def cleaner(text):
    """
    Removes extra spaces, symbols, and punctuation from string.
    
    Parameters: text - string
    Returns: a lowercased version of the string
    """


    text = text.replace('\n', ' ')
    text = re.sub('[^a-z A-Z0-9]', '', text)
    text = re.sub('[ ]{2,}', ' ', text).split()
    text = [word for word in text if not word.startswith(
        '@') and not word.startswith('http')]

    return ' '.join(text).lower().strip()


def topicizer(texts, num_topics = 5, len_topic_repr = 5):
    """
    Accepts a list of documents, cleans and transforms each document into a
    dimensional vector, then uses non-negative matrix factorization along with
    inverse document frequency, and singular value decomposition dimensionality
    reduction, to return a list of topics.
    Parameters:
    
      texts      - List of length two or greater. Each element in the list
                   is a sequence of at least three space separated words
      num_topics - Positive integer. The number of topics to present the entire
                   text. Will repeat topics if a large number is specified
                   but there is not enough data.
                  
      len_topic_repr - Positive integer. The number of words that will be used
                       to represent each topic.
    Returns: A list of topic representations, each is a list
             of the most influential words for the topic.
    """


    if len(texts) >= 2:
        texts = [cleaner(x) for x in texts]
        idfm = tfidf_vect.fit_transform(texts)
        nmf = NMF(n_components=num_topics, random_state=42)
        nmf.fit(idfm)
        nmf_topics = []
        for topic in nmf.components_:
            s = topic.argsort()[-len_topic_repr:]
            component_words = [tfidf_vect.get_feature_names_out()[i] for i in s]
            nmf_topics += [component_words]
        
        return '  |  '.join(' '.join(c) for c in nmf_topics)

    return 'Not enough text to analyze'