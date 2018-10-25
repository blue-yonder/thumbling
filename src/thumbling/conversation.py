""" the conversation logic for the thumbling bot

the module handles the incoming messages for the intent and creates corresponding
responses
"""


import aiohttp
from botbuilder.core import TurnContext, CardFactory
from botbuilder.schema import Activity, ActivityTypes, Attachment

from thumbling.cards import create_simple_alert_card
from thumbling.luis import get_message_intent
from thumbling import prometheus
from thumbling.utils import get_service_config


async def create_reply_activity(
    request_activity: Activity, text: str, attachment: Attachment = None
) -> Activity:
    activity = Activity(
        type=ActivityTypes.message,
        channel_id=request_activity.channel_id,
        conversation=request_activity.conversation,
        recipient=request_activity.from_property,
        from_property=request_activity.recipient,
        text=text,
        service_url=request_activity.service_url,
    )
    if attachment is not None:
        activity.attachments = [attachment]
    return activity


async def handle_problem_intent(context: TurnContext, message_intent: dict):
    """ if a message was categorized as a problem get the Prometheus alerts and respond

    Based on the intent entities create the Prometheus queries and time range.
    With the result create the message card for the response.
    Send one message(card) per instance/service entity and time range.
    """
    prometheus_config = get_service_config(
        context.adapter.settings.config["custom_services"],
        "prometheus",
        context.adapter.settings.environment,
    )
    prometheus_api = prometheus.PrometheusAPI(prometheus_config)
    query_strings = prometheus.get_alert_queries(message_intent["entities"])
    if not query_strings:
        await handle_unrecognized_intent(
            context,
            "Sorry, I was not able to determine which service you have a problem with.",
        )
    time_ranges = prometheus.get_query_time_ranges(message_intent["entities"])

    for time_range in time_ranges:
        for query_string in query_strings:
            try:
                result = await prometheus_api.query_range(
                    query_string, start=time_range[0], end=time_range[1]
                )
                card = create_simple_alert_card(result["data"]["result"], *time_range)
                response = await create_reply_activity(
                    context.activity,
                    "There were the following alerts:",
                    attachment=CardFactory.adaptive_card(card),
                )
            except aiohttp.client_exceptions.ClientConnectorError:
                response = await create_reply_activity(
                    context.activity,
                    "\U000026A0 There was a problem connecting the Prometheus server.",
                )
            await context.send_activity(response)


async def handle_unrecognized_intent(context: TurnContext, message: str):
    response = await create_reply_activity(context.activity, message)
    await context.send_activity(response)


async def handle_initial_message(context: TurnContext) -> aiohttp.web.Response:
    luis_service_config = get_service_config(
        context.adapter.settings.config["services"], "luis", "production"
    )
    # TODO handel the LuisError exception for too long messages
    message_intent = await get_message_intent(
        luis_service_config, context.activity.text
    )
    if (
        "topScoringIntent" in message_intent
        and message_intent["topScoringIntent"]["intent"] == "problem"
        and message_intent["topScoringIntent"]["score"] >= 0.8
    ):
        await handle_problem_intent(context, message_intent)
    else:
        await handle_unrecognized_intent(
            context, "Sorry, I did not understand. Please rephrase your concern."
        )


async def handle_conversation_update(context: TurnContext) -> aiohttp.web.Resource:
    message = "conversation update not implemented yet"
    response = await create_reply_activity(context.activity, message)
    await context.send_activity(response)


# entry point from the bot_server app
async def handle_message(context: TurnContext) -> aiohttp.web.Response:
    if not context.responded:
        await handle_initial_message(context)
    else:
        await handle_conversation_update(context)
    return aiohttp.web.Response(status=202)
