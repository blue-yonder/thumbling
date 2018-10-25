import time

from aiohttp import web
import iso8601


STARTUP_TIME = int(time.time())
ALERTS = [
    {
        "alertname": "ServiceDown",
        "severity": "page",
        "instance": "euler-p1",
        "service": "euler",
        "alert_time_offsets": [
            (-1900, -1500),
            (-3500, -3030),
            (-18200, -17900),
            (-100_000, -90500),
            (-150_500, -12000),
            (-270_500, -26700),
            (-650_500, -63700),
        ],
    },
    {
        "alertname": "SlowAnswerTimes",
        "severity": "warning",
        "instance": "euler-s1",
        "service": "euler",
        "alert_time_offsets": [
            (-4500, -3700),
            (-30500, -29730),
            (-45040, -44600),
            (-70000, -69000),
            (-120_115, -110_375),
            (-240_115, -236_375),
            (-540_115, -526_375),
        ],
    },
]


def get_alerts_in_range(query: str, start: int, end: int, step: int = 60) -> list:
    alerts_in_range = []
    for alert in ALERTS:
        if (
            f"service=\"{alert['service']}\"" not in query
            and f"instance=\"{alert['instance']}\"" not in query
        ):
            continue

        for offset_pair in alert["alert_time_offsets"]:
            values = []
            alert_start_time = STARTUP_TIME + offset_pair[0]
            alert_end_time = STARTUP_TIME + offset_pair[1]
            if (alert_end_time > start) or (end > alert_end_time):
                for t in range(
                    max(start, alert_start_time), min(end, alert_end_time), step
                ):
                    values.append([t, "1"])
            if values:
                result_entry = {"metric": {"__name__": "ALERTS"}, "values": values}
                result_entry["metric"].update(
                    {
                        key: value
                        for key, value in alert.items()
                        if key not in ["alert_time_offsets"]
                    }
                )
                alerts_in_range.append(result_entry)
    return alerts_in_range


def str2timestamp(t: str) -> int:
    try:
        return float(t)
    except ValueError:
        return iso8601.parse_date(t).timestamp()


async def query_range(request):
    if "start" in request.rel_url.query and "end" in request.rel_url.query:
        start = int(str2timestamp(request.rel_url.query["start"]))
        end = int(str2timestamp(request.rel_url.query["end"]))
        alerts = get_alerts_in_range(request.rel_url.query["query"], start, end)
    else:
        raise web.HTTPBadRequest(text="start and end required")

    response_body = {
        "status": "success",
        "data": {"resultType": "matrix", "result": alerts},
    }
    return web.json_response(response_body)


app = web.Application()
app.add_routes([web.get("/api/v1/query_range", query_range)])


if __name__ == "__main__":
    web.run_app(app, port=9000)
