#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import shutil
from glob import glob

import humanize
import requests
import requests_cache
from toolz import groupby

SUBTITLES = ["srt", "sfv", "sub"]
API_KEY = "ca62e3a"

everything = glob("**", recursive=True)
files = list(filter(os.path.isfile, everything))
directories = list(filter(os.path.isdir, everything))


def prompt():
    return input("Rename? [Y/n] : ").strip() in ["", "y", "Y"]


def multiple_subtitles(directory):
    files = []
    for file_ in os.listdir(directory):
        path = os.path.join(directory, file_)
        filename, _, extension = file_.rpartition(".")
        if os.path.isfile(path) and extension.lower() in SUBTITLES:
            files.append(file_)
    return len(files) > 1


def phase_one():
    for file_ in files:
        basename = os.path.basename(file_)
        filename, _, extension = basename.rpartition(".")
        new_filename = re.sub(r"^((?:19|20)\d\d) - (.*)", r"\2 \1", filename)
        new_filename = re.sub(r"^((?:19|20)\d\d) ", r"", new_filename)
        new_filename = re.sub(
            r"(.*?)((?:19|20)\d\d).*", r"\1 \2", new_filename
        )
        new_filename = re.sub(
            r"(.*?)(?:360|480|720|1080)[pP].*", r"\1", new_filename
        )
        new_filename = re.sub(r"[^\w',]+", " ", new_filename)
        new_filename = re.sub(r" (\w{3})$", r".\1", new_filename)
        new_filename = new_filename.replace("_", " ")
        new_filename = re.sub(
            r"(BRRip|BluRay|DVDivX|DVDrip|xvid).*",
            r"",
            new_filename,
            flags=re.IGNORECASE,
        )
        new_filename = re.sub(r"\s+", r" ", new_filename).strip()
        new_filename = re.sub(r"((?:19|20)\d\d)", r"(\1)", new_filename)
        new_filename = new_filename.replace("www UsaBit com ", "")

        re_object = re.search(r"(?:CD|cd)(\d)", file_)
        if re_object:
            new_filename = re.sub(r"\.( ?- ?)?(?:CD|cd)(\d)",
                                  "", new_filename).strip()
            new_filename += " - CD" + re_object.group(1)

        new_path = os.path.abspath(
            os.path.join(
                os.path.dirname(file_),
                "{}.{}".format(new_filename.title(), extension),
            ).replace("'S", "'s")
        ).replace("Cd", "CD")
        old_path = os.path.abspath(file_)
        print(old_path)
        continue
        if new_path != old_path:
            print("New: ", new_path)
            print("Old: ", old_path)
            print("\n")
            if prompt():
                print("Yes", new_path != old_path)
                shutil.move(old_path, new_path)


def name(file_):
    filename, _, extension = file_.rpartition(".")
    return filename


def grouper():
    for folder, files in groupby(name, os.listdir('.')).items():
        size = sum([os.stat(file_).st_size for file_ in files], 0)
        human_readable_size = humanize.naturalsize(size)
        print("{} - {}".format(folder, human_readable_size))


def get_movie(movie, year=None):
    params = {
        "t": movie,
        "type": "movie",
        "apikey": API_KEY,
        "year": year
    }

    if not params["year"]:
        params.pop('year')

    response = requests.get(
        "http://www.omdbapi.com/",
        params=params,
    )
    {
        "Response": "False",
        "Error": "Movie not found!"
    }
    return response.json()


def get_genre(movie, year=None):
    movie_info = get_movie(movie, year)
    return movie_info['Genre'].split(', ')[0]


def filename_to_genre(filename):
    try:
        movie, year = re.search(r'^(.*) \((\d{4})\)', filename).groups()
    except AttributeError:
        movie, year = name(filename), None

    try:
        return get_movie(movie, year)['Genre'].split(', ')[0]
    except KeyError:
        return "Unknown"


def group_by_genre(directory='.'):
    for filename in os.listdir(directory):
        if os.path.isdir(filename):
            continue
        genre = filename_to_genre(filename)
        os.makedirs(genre, exist_ok=True)
        shutil.move(filename, genre)
        print(filename, '|', genre)


requests_cache.install_cache('../omdb', backend='sqlite')

if __name__ == "__main__":
    # grouper()
    pass
