from os.path import expanduser
import os
import json

import re


def get_only_range(range_name):
    s = range_name.split("!")
    if len(s) > 1:
        return s[1]
    return range_name


def get_start_row(range_name):
    s = get_only_range(range_name)
    result = re.search("[a-zA-Z]([0-9]*).*", s)
    return int(result.groups()[0])


def placeholder_range_name(range_name):
    print(range_name)
    s = range_name.split("!")
    if len(s) > 1:
        result = re.sub('(\d+|$)', "{}", s[1])
        return s[0] + "!" + result
    else:
        return re.sub('(\d+|$)', "{}", range_name)


class PersistProperties:
    def __init__(self):
        home = expanduser("~")

        properties_dir = os.path.join(home, ".gnucashreport")
        self.properties_fname = os.path.join(properties_dir, "gnucashreport.properties")

        if not os.path.isdir(properties_dir):
            os.mkdir(properties_dir)

        if not os.path.exists(self.properties_fname):
            with open(self.properties_fname, 'w') as f:
                json.dump({}, f)

        with open(self.properties_fname) as f:
            try:
                self.props = json.load(f)
            except Exception as e:
                print(e)
                self.props = {}
                json.dump({}, f)

    def __getitem__(self, item):
        if item in self.props:
            return self.props[item]
        else:
            raise KeyError("{} is not a know property".format(item))

    def __setitem__(self, key, value):
        self.props[key] = value
        with open(self.properties_fname, "w") as f:
            json.dump(self.props, f)

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            return ""

    def set_property(self, key, value):
        self[key] = value
