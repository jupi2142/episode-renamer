#!/usr/bin/env python
# -*- coding: utf-8 -*-


def keep(dict_, keys):
    return {key: value for key, value in dict_.items() if key in keys}


def simplify_dicts(dicts):
    return [
        keep(dict_, ["Title", "Season", "No. inseason", "Number"])
        for dict_ in dicts
    ]
