from sqlalchemy import *

engine = create_engine('sqlite:///pins.db', echo=True)

metadata = MetaData()

image = Table('image', metadata, 
    Column('image_id', Integer, primary_key=True),
    Column('source_type', String),
    Column('filename', String),
    Column('height', Integer),
    Column('width', Integer),
)

tweet = Table('tweet', metadata,
    Column('tweet_id', Integer, primary_key=True),
    Column('tweet_created_at', String),
    Column('tweeter_id', Integer),
    Column('tweeter_handle', String, nullable=False),
)

tweetmap = Table('tweetmap', metadata,
    Column('image_id', Integer, ForeignKey('image.image_id')),
    Column('tweet_id', Integer, ForeignKey('tweet.tweet_id')),
)

metadata.create_all(engine)
