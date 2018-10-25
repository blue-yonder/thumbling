""" get and handle message intents from Microsoft Language Understanding LUIS

this module handles all around getting message intens from LUIS and
processing the results

see https://eu.luis.ai/home and https://docs.microsoft.com/en-us/azure/cognitive-services/luis/
"""

import aiohttp


COGNATIVE_API_BASE_URL = "api.cognitive.microsoft.com/luis/v2.0/apps"


class LuisError(Exception):
    """
    An error during language understanding with LUIS
    """


def create_luis_url(config: dict) -> str:
    """ use the luis section of the bot services to create the service URL
    """
    region = config.get("region", "westeurope")
    return f"https://{region}.{COGNATIVE_API_BASE_URL}/{config['appId']}"


async def get_message_intent(service_config: dict, sentence: str) -> dict:
    if len(sentence) > 500:
        raise LuisError(
            "the sentence is too long as it contains more than 500 characters"
        )

    headers = {"Ocp-Apim-Subscription-Key": service_config["subscriptionKey"]}
    params = {"q": sentence, "timezoneOffset": "0"}

    async with aiohttp.ClientSession() as session:
        async with session.get(
            create_luis_url(service_config), headers=headers, params=params
        ) as resp:
            return await resp.json()


def group_datetimeV2_entities(entities: list) -> dict:
    groups = {
        "date": [],
        "time": [],
        "daterange": [],
        "timerange": [],
        "datetimerange": [],
        "duration": [],
        "set": [],
    }
    for entity in entities:
        if entity["type"].startswith("builtin.datetimeV2."):
            datetime_type = entity["type"][len("builtin.datetimeV2.") :]
            groups[datetime_type].append(entity["resolution"]["values"])
    return groups
