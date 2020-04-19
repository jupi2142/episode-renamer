#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import operator as op
import os
import re
import shutil

import click
import requests
from bs4 import BeautifulSoup


URL_PATTERNS = (
    "https://en.wikipedia.org/wiki/list_of_{}_episodes",
    "https://en.wikipedia.org/wiki/{}",
)
EPISODES_TEMPLATE = os.path.join(
    os.path.dirname(__file__), "episodes", "{}.json"
)
STRIPPER_PATTERNS = (re.compile(r"^.*[eE](\d+)"),)


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

    # skip the row span
    # Four digit in seasons
    # row span


def keep(dict_, keys):
    return {key: value for key, value in dict_.items() if key in keys}


def episodes_list_to_json(episodes_list_url):
    print("Fetching: {}".format(episodes_list_url))
    episodes_list_html = requests.get(episodes_list_url).content
    # episodes_list_html = open("/tmp/list.html").read()
    soup = BeautifulSoup(episodes_list_html, features="lxml")
    [sup.extract() for sup in soup.select("sup.reference")]
    episode_list_tables = soup.find_all(episode_list_table_selector)
    dicts = []
    for season, table in enumerate(episode_list_tables, 1):
        print("Season: ", season)
        for dict_ in table_to_dict(table):
            try:
                dict_["Number"] = int(
                    (dict_.pop("No. inseason", None) or dict_.pop("No.", None))
                )
            except (ValueError, TypeError):
                import pprint

                pprint.pprint(dict_)
                continue
            dict_["Title"] = dict_.pop("Title").strip('"')
            dict_["Season"] = season
            dicts.append(dict_)

    return dicts


def simplify_dicts(dicts):
    return [
        keep(dict_, ["Title", "Season", "No. inseason", "Number"])
        for dict_ in dicts
    ]


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


def load_episodes(series):
    series = series.lower().replace(" ", "_")
    series_json = EPISODES_TEMPLATE.format(series)
    urls = [url_pattern.format(series) for url_pattern in URL_PATTERNS]
    try:
        dicts = json.load(open(series_json))
    except (ValueError, TypeError, IOError):
        dicts = episodes_list_to_json(urls[0]) or episodes_list_to_json(
            urls[1]
        )
    dicts = process_doubles(dicts)
    dicts = simplify_dicts(dicts)
    json.dump(dicts, open(series_json, "w+"), indent=2)
    print("Episodes loaded")
    return dicts


@click.command()
@click.argument("series")
@click.option("--rename", is_flag=True)
@click.option("--force", is_flag=True)
@click.option("--check", is_flag=True)
@click.option("--bulk", is_flag=True)
# TODO: GROUP, match and download
def main(series, **kwargs):
    episodes = load_episodes(series)
    import ipdb
    ipdb.set_trace()
    # Don't show the "renamed" thing for "bulk and/or force"
    # find a way to strip filenames to just the episode number (pattern lists)
    # find a way to use it for a whole folder
    # change how episodes are used as index (^\d+)\D

    if not kwargs["rename"]:
        return

    season = int(re.search(r"Season 0*(\d+)$", os.getcwd()).group(1))

    episodes_for_this_season = {
        episode["Number"]: episode
        for episode in episodes
        if episode["Season"] == season
    }

    pattern = re.compile(r"^0*(?P<Number>\d+).*\.(?P<extension>[\w]+)")
    for file_name in os.listdir("."):
        try:
            number, extension = pattern.search(file_name).groups()
        except AttributeError:
            continue
        try:
            episode = episodes_for_this_season[int(number)]
        except KeyError as e:
            print(e)
            continue
        new_file_name = (
            u"{number} - {title}.{extension}".format(
                number=number.zfill(2),
                title=episode["Title"],
                extension=extension,
            )
            .replace(":", "--")
            .replace("/", "--")
        )
        print("\t->\t".join([file_name, new_file_name]))
        if kwargs["check"]:
            continue
        if kwargs["force"] or (
            raw_input("Rename [Y/n] : ").strip() in ["", "y", "Y"]
        ):
            shutil.move(file_name, new_file_name)
            if not (kwargs['bulk'] or kwargs['force']):
                print("Renamed")
        else:
            print("Skipped")


# def match
#   strip the starting 0

if __name__ == "__main__":
    main()
