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
    os.path.dirname(os.path.realpath(__file__)), "episodes", "{}.json"
)
FILENAME_PATTERN = re.compile(
    r"^(?:.*(?:[eE]p?|\d+x))?0*(?P<Number>\d+).*\.(?P<extension>[\w]+)"
)
SEASON_PATTERN = re.compile(r"[sS]eason 0*(\d+)$")


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
    try:
        episodes_list_html = requests.get(episodes_list_url).content
    except requests.exceptions.ConnectionError:
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


def load_episodes(series, fallback_url=""):
    series = series.replace(" ", "_")
    series_json = EPISODES_TEMPLATE.format(series)
    urls = [url_pattern.format(series) for url_pattern in URL_PATTERNS]
    try:
        dicts = json.load(open(series_json))
    except (ValueError, TypeError, IOError):
        dicts = (
            episodes_list_to_json(fallback_url) or
            episodes_list_to_json(urls[0]) or
            episodes_list_to_json(urls[1])
        )

    dicts = process_doubles(dicts)
    dicts = simplify_dicts(dicts)
    json.dump(dicts, open(series_json, "w+"), indent=2)
    print("Episodes loaded")
    return dicts


def prompt():
    return raw_input("Rename? [Y/n] : ").strip() in ["", "y", "Y"]


def default_seasons():
    cwd = os.getcwd()
    season_folders = filter(SEASON_PATTERN.search, [cwd]) + filter(
        SEASON_PATTERN.search, os.listdir(cwd)
    )

    return [
        int(SEASON_PATTERN.search(season_folder).group(1))
        for season_folder in season_folders
    ]


def rename_for_season(season, episodes, rename_type, path):
    episodes_for_this_season = {
        episode["Number"]: episode
        for episode in episodes
        if episode["Season"] == season
    }

    to_rename = []

    file_names = map(op.methodcaller("decode", "utf-8"), os.listdir(path))
    print("Path: {}".format(path))

    for file_name in file_names:
        try:
            number, extension = FILENAME_PATTERN.search(file_name).groups()
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
                extension=extension.lower(),
            )
            .replace(":", "--")
            .replace("/", "--")
            .replace(u'"†', "")
        )
        try:
            print(u"\t->\t".join([file_name, new_file_name]))
        except UnicodeDecodeError:
            continue

        file_name = os.path.join(path, file_name)
        new_file_name = os.path.join(path, new_file_name)

        if rename_type == "single" and prompt():
            shutil.move(file_name, new_file_name)
        elif rename_type in ["bulk", "bulk-force"]:
            to_rename.append((file_name, new_file_name))

    if rename_type == "bulk-force" or (rename_type == "bulk" and prompt()):
        for file_name, new_file_name in to_rename:
            shutil.move(file_name, new_file_name)


@click.command()
@click.argument("series")
@click.option("-u", "--url", default="https://www.wikipedia.com")
@click.option(
    "-r",
    "--rename-type",
    type=click.Choice(["check", "single", "bulk", "bulk-force"]),
    default="check",
)
@click.option("-s", "--seasons", default=default_seasons)
def main(series, rename_type, seasons, **kwargs):
    episodes = load_episodes(series, kwargs["url"])
    parent_folder = SEASON_PATTERN.sub("", os.getcwd())
    for season in seasons:
        path = os.path.join(parent_folder, "Season {}".format(season))
        rename_for_season(season, episodes, rename_type, path)


if __name__ == "__main__":
    main()
