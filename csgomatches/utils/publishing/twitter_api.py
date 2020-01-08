import os

def get_twitter_credentials():
    cred_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'twitter_credentials.txt')
    consumer_key, consumer_secret, access_token_key, access_token_secret = "", "", "", ""

    with open(cred_file_path, 'r') as cred_file:
        s = cred_file.read()
        consumer_key, consumer_secret, access_token_key, access_token_secret = s.split(",")
    return consumer_key, consumer_secret, access_token_key, access_token_secret


#print("Init Twitter Api for key", consumer_key)

# users = api.GetFriends()
# print([s.name for s in users])

# status = api.PostUpdate('Willkommen beim Twitter-Account von wannspieltbig.de\n\nHeute steht der EU Open Qualifier #2 für IEM Katowice 2020 ab ca. 18:00 Uhr an.')
