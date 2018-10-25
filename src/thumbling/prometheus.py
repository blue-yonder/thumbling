""" Prometheus querying and result transformation

The module provides functionality to query a Prometheus server and
helpers to create correct query parameters.
"""


from datetime import datetime, timedelta
import time
from typing import Union

import aiohttp

from thumbling.luis import group_datetimeV2_entities
from thumbling.utils import str2timestamp


Num = Union[int, float]


class PrometheusAPI:
    """ Query a Prometheus server API

    see https://prometheus.io/docs/prometheus/latest/querying/api/
    """

    def __init__(self, service_config: dict):
        if service_config["endpoint"].endswith("/"):
            self.base_url = service_config["endpoint"][:-1]
        else:
            self.base_url = service_config["endpoint"]

        self.query_url = self.base_url + "/api/v1/query"
        self.query_range_url = self.base_url + "/api/v1/query_range"

    async def query(
        self, query_string: str, time: str = None, timeout: int = None
    ) -> dict:
        params = {"query": query_string}
        if time is not None:
            params["time"] = str2timestamp(time)
        if timeout is not None:
            params["timeout"] = timeout
        async with aiohttp.ClientSession() as session:
            async with session.get(self.query_url, params=params) as resp:
                return await resp.json()

    async def query_range(
        self,
        query_string: str,
        start: str,
        end: str,
        step: str = "1m",
        timeout: int = None,
    ) -> dict:
        params = {"query": query_string, "step": step}
        if timeout is not None:
            params["timeout"] = timeout
        params["start"] = start
        params["end"] = end
        async with aiohttp.ClientSession() as session:
            async with session.get(self.query_range_url, params=params) as resp:
                return await resp.json()


def get_limited_time_range(start: Num, end: Num, safety: int = 30) -> (int, int):
    """ limited a time range to values in the past

    Prometheus does not allow timestamps in its future so cut off the end
    or return None if the start is before the end or in the future.
    """
    now = time.time()
    start = min(start, now - safety)
    end = min(end, now - safety)
    if start >= now or start >= end:
        return None
    return int(start), int(end)


def get_query_time_ranges(entities: list) -> list:
    """ transform intent entities datetimeV2 to timestap tuples

    A very incomplete and faulty implementation of datetimeV2 entities
    to Prometheus valid timestamp tuples for the start/end query parameters.
    There must be better solutions.
    """
    time_entities = group_datetimeV2_entities(entities)
    time_ranges = []
    for subtype in time_entities:
        if subtype == "time":
            for entity in time_entities[subtype]:
                for value in entity:
                    # use a 10 minutes time window
                    time_value = datetime.combine(
                        datetime.today(),
                        datetime.strptime(value["value"], "%H:%M:%S").time(),
                    ).timestamp()
                    time_range = get_limited_time_range(
                        time_value - 300, time_value + 300
                    )
                    if time_range is not None:
                        time_ranges.append(time_range)
        elif subtype == "date":
            for entity in time_entities[subtype]:
                for value in entity:
                    start_time = datetime.strptime(value["value"], "%Y-%m-%d")
                    end_time = start_time + timedelta(days=1)
                    time_range = get_limited_time_range(
                        start_time.timestamp(), end_time.timestamp()
                    )
                    if time_range is not None:
                        time_ranges.append(time_range)
        elif subtype in ["daterange", "datetimerange"]:
            for entity in time_entities[subtype]:
                for value in entity:
                    if "end" not in value:
                        value["end"] = int(time.time())
                    start_time = str2timestamp(value["start"])
                    end_time = str2timestamp(value["end"])
                    time_range = get_limited_time_range(start_time, end_time)
                    if time_range is not None:
                        time_ranges.append(time_range)
        elif subtype in "timerange":
            for entity in time_entities[subtype]:
                for value in entity:
                    if "end" not in value:
                        end_time = int(time.time())
                    else:
                        end_time = datetime.combine(
                            datetime.today(),
                            datetime.strptime(value["end"], "%H:%M:%S").time(),
                        ).timestamp()
                    start_time = datetime.combine(
                        datetime.today(),
                        datetime.strptime(value["start"], "%H:%M:%S").time(),
                    ).timestamp()
                    time_range = get_limited_time_range(start_time, end_time)
                    if time_range is not None:
                        time_ranges.append(time_range)
    return time_ranges


def get_alert_queries(entities: list) -> list:
    """ create the value for the Prometheus query parameter based on the entities

    This is also very rudimentary and must probably adapted to each ones use case.
    """
    instance_entities = [e for e in entities if e["type"] == "instance"]
    if instance_entities:
        queries = []
        for entity in instance_entities:
            instance = entity["entity"].replace(" ", "")
            queries.append(f'ALERTS{{instance="{instance}"}}')
        return queries

    # if we do not have specific search targets we use the less specific ones
    service_name_entities = [e for e in entities if e["type"] == "service-name"]
    if service_name_entities:
        queries = []
        for entity in service_name_entities:
            queries.append(f'ALERTS{{service="{entity["entity"]}"}}')
        return queries

    return []
