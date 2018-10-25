from thumbling.cards import create_simple_alert_card


ALERTS = [
    {
        "metric": {
            "__name__": "ALERTS",
            "alertname": "SlowAnswerTimes",
            "severity": "warning",
            "instance": "euler-s1",
            "service": "euler",
        },
        "values": [
            [1540251900, "1"],
            [1540251960, "1"],
            [1540252020, "1"],
            [1540252080, "1"],
            [1540252140, "1"],
            [1540252200, "1"],
            [1540252260, "1"],
        ],
    },
    {
        "metric": {
            "__name__": "ALERTS",
            "alertname": "ServiceDown",
            "severity": "page",
            "instance": "euler-p1",
            "service": "euler",
        },
        "values": [
            [1540251900, "1"],
            [1540251960, "1"],
            [1540252020, "1"],
            [1540252080, "1"],
            [1540252140, "1"],
            [1540252200, "1"],
            [1540252260, "1"],
        ],
    },
]


def test_create_simple_alert_card():
    result = create_simple_alert_card(ALERTS, 1540000000, 1541000000)
    expected = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.0",
        "type": "AdaptiveCard",
        "body": [
            {
                "type": "TextBlock",
                "size": "Medium",
                "wrap": True,
                "text": "2018-10-20 03:46:40 - 2018-10-31 16:33:20",
            },
            {
                "type": "Container",
                "seperator": True,
                "items": [
                    {
                        "type": "TextBlock",
                        "wrap": True,
                        "text": "2018-10-23 01:45:00 - 2018-10-23 01:51:00",
                    },
                    {
                        "type": "TextBlock",
                        "horizontalAlignment": "right",
                        "text": "SlowAnswerTimes",
                    },
                    {
                        "type": "TextBlock",
                        "wrap": True,
                        "text": "2018-10-23 01:45:00 - 2018-10-23 01:51:00",
                    },
                    {
                        "type": "TextBlock",
                        "horizontalAlignment": "right",
                        "text": "ServiceDown",
                    },
                ],
            },
        ],
    }
    assert result == expected
