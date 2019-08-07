import re
import datetime as dt
import twitter as tw
import os
import requests
import xml.etree.ElementTree as etree
import urllib


FEED = 'http://www.thisday.pcahistory.org/feed/'
USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'
DATE_PATTERN = "%a, %d %b %Y  %H:%M:%S +0000"


def save_image(url):
    filename = url[url.rfind("/")+1:]
    img_path = f"/tmp/{filename}"
    urllib.request.retrieve(url, img_path)
    return img_path


class ElementWrapper:

    def __init__(self, element):
        self._element = element

    def __getattr__(self, tag):
        if tag.startswith("__"):
            raise AttributeError(tag)
        return self._element.findtext(tag)


def get_image_url(item):
    i = item._element.find('{http://purl.org/rss/1.0/modules/content/}encoded')
    images = re.findall("data-orig-file=\"(.*?)\"", str(i.text))
    if len(images) > 0:
        return images[0]


def get_feed(feed):
    r = requests.get(feed,
                     headers={
                         'User-Agent': USER_AGENT,
                     }
                     )
    return etree.fromstring(r.text)


def get_today(feed):
    for item in feed.findall("channel/item"):
        item = ElementWrapper(item)
        pubdate = dt.datetime.strptime(item.pubDate, DATE_PATTERN).date()
        if pubdate == dt.datetime.now().date():
            title = item.title.split(":", maxsplit=1)[1]
            return title, item.link, get_image_url(item)
    return None, None, None


def update_facebook(title, url):
    import facebook
    api = facebook.GraphAPI(os.environ["FACEBOOK_SECRET"].strip())

    try:
        api.put_object(
            parent_object="me",
            connection_name="feed",
            message=f"Today in OPC History: {title}",
            link=url
        )
        return "Successfully posted to Facebook"
    except facebook.GraphAPIError as e:
        return "Error", e


def update_twitter(title, url, image_url):
    cred = {
        "consumer_key": os.environ["CONSUMER_KEY"].strip(),
        "consumer_secret": os.environ["CONSUMER_SECRET"].strip(),
        "token": os.environ["TOKEN"].strip(),
        "token_secret": os.environ["TOKEN_SECRET"].strip(),
    }
    auth = tw.OAuth(**cred)
    t = tw.Twitter(auth=auth)
    status = f"{title} {url} #PCAhistory"
    try:
        if image_url is not None:
            req = urllib.request.Request(
                url,
                data=None,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
                }
            )
            image = urllib.request.urlopen(req, timeout=10).read()
            media = t.media.upload(media=image)
            t.statuses.update(status=status, media_ids=media['media_id_string'])
        else:
            t.statuses.update(status=status)
        return "Tweeted {}".format(status)
    except Exception as e:
        return e


def update(event=None, context=None):
    feed = get_feed(FEED)
    title, url, image_url = get_today(feed)
    fb_log = update_facebook(title, url)
    twitter_log = update_twitter(title, url, image_url)
    return "{}; {}".format(fb_log, twitter_log)


if __name__ == '__main__':
    print(update())
