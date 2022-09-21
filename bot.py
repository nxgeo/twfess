from re import compile, escape

from flask import Flask, request
from tweepy import API, Forbidden, OAuth1UserHandler

API_KEY = ""
API_KEY_SECRET = ""
ACCESS_TOKEN = ""
ACCESS_TOKEN_SECRET = ""

TRIGGER_WORD = ""


auth = OAuth1UserHandler(
    API_KEY, API_KEY_SECRET,
    ACCESS_TOKEN, ACCESS_TOKEN_SECRET
)

api = API(auth, wait_on_rate_limit=True)

base = api.verify_credentials()

trigger_word_pattern = compile(rf"\A{escape(TRIGGER_WORD)}\s")
tweet_permalink = "https://twitter.com/{}/status/{{}}".format(base.screen_name)


def handle_dm(dm):
    message_data = dm["message_create"]["message_data"]
    text = message_data["text"]
    if (not trigger_word_pattern.match(text)
            or any(message_data["entities"].values())
            or "attachment" in message_data):
        return
    try:
        tweet = api.update_status(text, trim_user=True)
    except Forbidden:
        # handle 186 and 187
        pass
    else:
        api.send_direct_message(
            dm["message_create"]["sender_id"],
            f"Tweeted! {tweet_permalink.format(tweet.id_str)}"
        )


app = Flask(__name__)


@app.post("/webhook")
def handle_event():
    payload = request.json
    if (payload["for_user_id"] == base.id_str
            and "direct_message_events" in payload):
        for dm in payload["direct_message_events"]:
            if (dm["type"] == "message_create"
                    and dm["message_create"]["target"]["recipient_id"] == base.id_str):
                handle_dm(dm)
    return "", 204


if __name__ == "__main__":
    app.run()
