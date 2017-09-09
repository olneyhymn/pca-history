try:
    import re
except:
    print("re fail")
import datetime as dt
try:
    import twitter as tw
except:
    print("twitter fail")
import json
try:
    import requests
except:
    print("requests fail")
try:
    import xml.etree.ElementTree as etree
except:
    print("xml fail")

FEED = 'http://www.thisday.pcahistory.org/feed/'
USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'
DATE_PATTERN = "%a, %d %b %Y  %H:%M:%S +0000"


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
    with open('facebook.txt', 'r') as f:
        access_token = f.read().strip()
    api = facebook.GraphAPI(access_token)

    try:
        api.put_wall_post("", attachment={"link": url, "name": title})
        return "Successfully posted to Facebook"
    except facebook.GraphAPIError as e:
        return "Error", e


def update_twitter(title, url, image_url):
    with open("twitter.json", "r") as f:
        credentials = json.load(f)
    t = tw.Api(**credentials)
    try:
        status = "{} {}".format(title, url)
        if image_url is not None:
            t.PostMedia(status, image_url)
        else:
            t.PostUpdate(status)
        return "Tweeted {}".format(status)
    except Exception as e:
        return e.message


def update(event=None, context=None):
    feed = get_feed(FEED)
    title, url, image_url = get_today(feed)
    # fb_log = update_facebook(title, url)
    twitter_log = update_twitter(title, url, image_url)
    # return "{}; {}".format(fb_log, twitter_log)


if __name__ == '__main__':
    print(update())
