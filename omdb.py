#!/usr/bin/env python
# -*- coding: utf-8 -*-
from itertools import count

import requests
import requests_cache
import os

from misc import simplify_dicts

cache = os.path.join(os.path.dirname(os.path.realpath(__file__)), "omdb")
requests_cache.install_cache(cache, backend='sqlite')  # , expire_after=300)

API_KEY = "ca62e3a"


def get_season(series, season=1):
    response = requests.get(
        "http://www.omdbapi.com/",
        params={
            "t": series,
            "type": "series",
            "apikey": API_KEY,
            "season": season,
        },
    )
    result = response.json()
    for episode in result["Episodes"]:
        episode["Season"] = int(result["Season"])
        episode["Number"] = int(episode["Episode"])
    return result["Episodes"]


def search_series(series):
    return requests.get(
        "http://www.omdbapi.com/",
        params={"s": series, "type": "series", "apikey": API_KEY},
    ).json()


def get_all_episodes(series, *args, **kwargs):
    episodes = []
    for season in count(1):
        print("Season {}".format(season))
        try:
            episodes.extend(
                [
                    episode
                    for episode in get_season(series, season)
                    if episode["imdbRating"] != "N/A"
                ]
            )
        except KeyError:
            break
    return simplify_dicts(episodes)


load_episodes = get_all_episodes
