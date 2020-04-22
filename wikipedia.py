#!/usr/bin/env python
# -*- coding: utf-8 -*-
import operator as op
import os

import requests
import requests_cache
from bs4 import BeautifulSoup

from misc import simplify_dicts

cache = os.path.join(os.path.dirname(os.path.realpath(__file__)), "omdb")
requests_cache.install_cache(cache, backend='sqlite')  # , expire_after=300)

URL_PATTERNS = (
    "https://en.wikipedia.org/wiki/list_of_{}_episodes",
    "https://en.wikipedia.org/wiki/{}",
)


def process_doubles(dicts):
    for dict_ in dicts:
        if dict_["Number"] > 99:
            one, two = divmod(dict_["Number"], 100)
            dict_["Number"] = one
            yield dict_
            dict_["Number"] = two
            yield dict_
        else:
            yield dict_


def episode_list_table_selector(tag):
    return tag.name == "table" and "Title" in tag.text


def table_to_dict(table):
    row_names = list(
        map(op.attrgetter("text"), table.find("tr").find_all("th"))
    )

    return [
        {
            row_name.strip(): td.text
            for row_name, td in zip(row_names, tr.find_all(["th", "td"]))
        }
        for tr in table.find_all("tr")[1:]
    ]


def episodes_list_to_json(episodes_list_url):
    print("Fetching: {}".format(episodes_list_url))
    try:
        episodes_list_html = requests.get(episodes_list_url).content
    except requests.exceptions.ConnectionError:
        return []
    except requests.exceptions.MissingSchema:
        return []
    # episodes_list_html = open("/tmp/list.html").read()
    soup = BeautifulSoup(episodes_list_html, features="lxml")
    [sup.extract() for sup in soup.select("sup.reference")]
    episode_list_tables = soup.find_all(episode_list_table_selector)
    dicts = []
    for season, table in enumerate(episode_list_tables, 1):
        print("Season: {}".format(season))
        for dict_ in table_to_dict(table):
            try:
                dict_["Number"] = int(
                    dict_.pop("No. inseason", None)
                    or dict_.pop("No. inseries", None)
                    or dict_.pop("No.", None)
                )
            except (ValueError, TypeError):
                # import pprint

                # pprint.pprint(dict_)
                continue
            dict_["Title"] = dict_.pop("Title").strip('"')
            dict_["Season"] = season
            dicts.append(dict_)

    return dicts


def load_episodes(series, fallback_url=""):
    series = series.replace(" ", "_")
    for url_pattern in URL_PATTERNS:
        dicts = episodes_list_to_json(url_pattern.format(series))
        if dicts:
            dicts = process_doubles(dicts)
            dicts = simplify_dicts(dicts)
            print("Episodes loaded")
            return dicts
    return []
