#!/usr/bin/env python
# -*- coding: utf-8 -*-

import operator as op
import os
import re
import shutil

import click


FILENAME_PATTERN = re.compile(
    r"^(?:.*(?:[eE]p?|\d+x))?0*(?P<Number>\d+).*\.(?P<extension>[\w]+)"
)
SEASON_PATTERN = re.compile(r"[sS]eason 0*(\d+)$")


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


# TODO: zenety and episode namer to integrate with thunar


@click.command()
@click.argument("series")
@click.option("-u", "--url", default="")
@click.option("--source",
              type=click.Choice(["omdb", "wikipedia"]),
              default="omdb")
@click.option(
    "-r",
    "--rename-type",
    type=click.Choice(["check", "single", "bulk", "bulk-force"]),
    default="check",
)
@click.option("-s", "--seasons", default=default_seasons)
def main(series, rename_type, seasons, source, **kwargs):
    if source == "omdb":
        from omdb import load_episodes
    else:
        from wikipedia import load_episodes
    episodes = load_episodes(series, kwargs["url"])
    parent_folder = SEASON_PATTERN.sub("", os.getcwd())
    for season in seasons:
        try:
            season_folder = "Season {}".format(int(season))
        except ValueError:
            season_folder, season = '.', 1
        path = os.path.join(parent_folder, season_folder)
        rename_for_season(season, episodes, rename_type, path)


if __name__ == "__main__":
    main()
