""" card attachments for message attachments

the module provides helpers to create the input for the botbuilder card creators

For more information, docu and designer see https://adaptivecards.io/
"""

import copy
from datetime import datetime


BASE_ADAPTIVE_CARD = {
    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
    "version": "1.0",
    "type": "AdaptiveCard",
}


def create_simple_alert_card(alerts: list, start: int, end: int) -> dict:
    container_items = []
    for alert in alerts:
        timestamps = [value[0] for value in alert["values"]]
        min_time = datetime.fromtimestamp(min(timestamps))
        max_time = datetime.fromtimestamp(max(timestamps))
        container_items.append(
            {"type": "TextBlock", "wrap": True, "text": f"{min_time} - {max_time}"}
        )
        container_items.append(
            {
                "type": "TextBlock",
                "horizontalAlignment": "right",
                "text": f"{alert['metric']['alertname']}",
            }
        )
    card = copy.copy(BASE_ADAPTIVE_CARD)
    start_time = datetime.fromtimestamp(start)
    end_time = datetime.fromtimestamp(end)
    card["body"] = [
        {
            "type": "TextBlock",
            "size": "Medium",
            "wrap": True,
            "text": f"{start_time} - {end_time}",
        },
        {"type": "Container", "seperator": True, "items": container_items},
    ]
    return card
