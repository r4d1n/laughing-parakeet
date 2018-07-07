import auth, json, requests, re, time, os, shutil
from sqlalchemy import create_engine, exc, MetaData, Table, select, desc

from PIL import Image
from io import BytesIO

with open('config.json', 'r') as f:
    config = json.load(f)

# db stuff
engine = create_engine(config['db_connection_string'], echo=False)
meta = MetaData(bind=engine)
conn = engine.connect()
# tables
tweet = Table('tweet', meta, autoload=True, autoload_with=engine)
image = Table('image', meta, autoload=True, autoload_with=engine)
tweetmap = Table('tweetmap', meta, autoload=True, autoload_with=engine)

# handle api interactions
pinboard_base_url = 'https://api.pinboard.in/v1/posts/all'
pinboard_params = {'auth_token': config['pinboard']['auth_token'], 'format': 'json'}
pins = requests.get(pinboard_base_url, pinboard_params)
pins_json = pins.json()

twitter_token = auth.get_twitter_token()
twitter_headers = {
    'Authorization': 'Bearer {}'.format(twitter_token)    
}

# get pinned links to tweets
tweet_links = [p['href'] for p in pins_json if re.search('twitter.com', p['href'])]

# parse out the tweet IDs
id_pattern = re.compile(r'/status/(\d+)/')
tweet_ids = []
for href in tweet_links:
    result = id_pattern.search(href)
    if result and result.group(1):
        tweet_ids.append(int(result.group(1)))
tweet_ids.sort()
# skip previously saved tweets
last_select = select([tweet.c.tweet_id]).order_by(desc(tweet.c.tweet_id)).limit(1)
last_result = conn.execute(last_select).fetchone()

if (last_result):
    last_saved_id = last_result['tweet_id']
    print('Last saved tweet {}'.format(last_saved_id))
    next_index = tweet_ids.index(last_saved_id) + 1
    print(next_index, len(tweet_ids))
    tweet_ids = tweet_ids[next_index:]

print('Will fetch {} tweets'.format(len(tweet_ids)))

# tweets by id endpoint
statuses_url = 'https://api.twitter.com/1.1/statuses/show.json'

img_pattern = re.compile(r'/media/(.+\.jpg|.+\.png)')

path_prefix = config['media_storage_path']

# parse media from twitter data and save
for uid in tweet_ids:
    params = {'id': uid}
    print('Fetching tweet: {}'.format(uid))
    resp = requests.get(statuses_url, headers=twitter_headers, params=params)
    tweet_json = resp.json()
    if 'extended_entities' not in tweet_json:
        continue
    if 'media' in tweet_json['extended_entities']:
        try:
            print('Tweet {} has {} media objects'.format(uid, len(tweet_json['extended_entities']['media'])))
            tweet_insert = tweet.insert().values(
                tweet_id = uid,
                tweet_created_at = tweet_json['created_at'],
                tweeter_id = tweet_json['user']['id'],
                tweeter_handle = tweet_json['user']['screen_name'],
            )
            conn.execute(tweet_insert)
            for media in tweet_json['extended_entities']['media']:
                if media['type'] == 'photo':
                    fname = img_pattern.search(media['media_url_https']).group(1)
                    path = '{}/{}'.format(path_prefix, fname)
                    dimensions = media['sizes']['large']
                    print('Fetching image {}'.format(media['media_url_https']))
                    imgr = requests.get(media['media_url_https'])
                    if imgr.status_code == 200:
                        i = Image.open(BytesIO(imgr.content))
                        print('Saving file {}'.format(path))
                        i.save(path)
                        image_insert = image.insert().values(
                            source_type = 'tweet',
                            filename = fname,
                            height = dimensions['h'],
                            width = dimensions['w'],
                        )
                        image_result = conn.execute(image_insert)
                        image_key = image_result.inserted_primary_key[0]
                        tweetmap_insert = tweetmap.insert().values(
                            image_id = image_key,
                            tweet_id = uid,
                        )
                        conn.execute(tweetmap_insert)
                        print('Finished tweet {}'.format(uid))
                    else:
                        print('Bad HTTP Status {} for image {} from tweet {}'.format(imgr.status_code, media['media_url_https'], uid))
        except Exception as err:
            print(err)
    time.sleep(1)
conn.close()
