import os
import json
from typing import Optional

from twitchAPI.twitch import Twitch
from twitchAPI.helper import first


def _read_twitch_credentials():
    cred_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'twitch_credentials.json')
    with open(cred_file_path, 'r') as cred_file:
        credentials = json.load(cred_file)
    return credentials['client_id'], credentials['client_secret']

class TwitchScraper:
    def __init__(self, twitch: Twitch):
        self._twitch = twitch

    @classmethod
    async def create(cls):
        app_id, app_secret = _read_twitch_credentials()
        twitch = await Twitch(app_id=app_id, app_secret=app_secret)
        self = cls(twitch)
        return self

    async def get_user_profile_image_url(self, user_name: str) -> Optional[str]:
        """
        Get the profile picture URL of a Twitch user by their user ID.
        """
        user = await first(self._twitch.get_users(logins=[user_name]))
        if user:
            return user.profile_image_url
        return None
