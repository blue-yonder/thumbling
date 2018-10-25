""" bot app and entry logic to handel incoming messages

The module for the bot aiohttp app and the logic to handel incoming messages.

To run the bot:

    $ python bot_server.py
"""

import os

from aiohttp import web
from botbuilder.schema import Activity
from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    TurnContext
    # currently not used
    # ConversationState,
    # MemoryStorage
    ,
)

from thumbling.conversation import handle_message
from thumbling.utils import load_bot_file, get_service_config


class ThumblingBotAdpaterSettings(BotFrameworkAdapterSettings):
    """ extended adapter settings to have the bot config available in each TurnContext

    With Adapter initialization the .bot configuration file is loaded as well,
    and based on the environment the app settings provide to it.
    The complete configuration is also stored in the config property.
    """

    def __init__(self):
        self.config = load_bot_file(
            os.getenv("botFilePath", default="./thumbling.bot"),
            os.getenv("botFileSecret"),
        )
        self.environment = os.getenv("APP_ENVIRONMENT", default="development")
        app_id = get_service_config(
            self.config["services"], "endpoint", self.environment
        )["appId"]
        app_password = get_service_config(
            self.config["services"], "endpoint", self.environment
        )["appPassword"]
        super().__init__(app_id, app_password)


SETTINGS = ThumblingBotAdpaterSettings()
ADAPTER = BotFrameworkAdapter(SETTINGS)

# currently not used
# memory = MemoryStorage()
# conversation_state = ConversationState(memory)
# ADAPTER.use(conversation_state)


async def unhandled_activity() -> web.Response:
    return web.Response(status=404)


async def request_handler(context: TurnContext) -> web.Response:
    if context.activity.type == "message":
        return await handle_message(context)
    else:
        return await unhandled_activity()


async def messages(req: web.web_request) -> web.Response:
    body = await req.json()
    activity = Activity().deserialize(body)
    auth_header = req.headers["Authorization"] if "Authorization" in req.headers else ""
    return await ADAPTER.process_activity(activity, auth_header, request_handler)


# we use "/api/messages" as it seems to be the "standard" URL used by bots
app = web.Application()
app.add_routes([web.post("/api/messages", messages)])


# for simple local execution only
if __name__ == "__main__":
    web.run_app(app, port=8000)
