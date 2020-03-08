#!/usr/bin/env python3
import argparse
from pathlib import Path
import re
import json
from subprocess import run, PIPE
from typing import Optional


Reason = str

# TODO ugh. need to test it properly...

BLOB_RE = r'https?://github.com/\w+/\w+/blob/[0-9a-z]{40}(/[\w\.]+)*'
# eliminate false positives like this:
# https://github.com/oshev/colifer/blob/592cc6b4d1ac9005c52fccdfb4e207513812baaa/reportextenders/jawbone/jawbone_sleep.py
def is_git_blob(string: str, json) -> Optional[Reason]:
    diff = json['diff']
    for line in diff.splitlines():
        occurence = line.find(string)
        if occurence == -1:
            continue

        if line.find(string, occurence + 1) != -1:
            raise RuntimeError("TODO handle multiple occurences later", line)

        # these define 'safe' regions
        for m in re.finditer(BLOB_RE, line):
            (fr, to) = m.span()
            if fr <= occurence < to:
                return f'Occuring in: {line}'
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument('repo', type=Path)
    p.add_argument('rest', nargs=argparse.REMAINDER)
    args = p.parse_args()
    res = run([
        'trufflehog',
        '--json',
        # TODO no-json argument? would be nice to have a nice way of displaying...
        # TODO maybe, parse both?
        args.repo,
        *args.rest,
    ], stdout=PIPE)
    if res.returncode > 1:
        res.check_returncode()

    jsons = [json.loads(x) for x in res.stdout.decode('utf8').splitlines()]

    # TODO logging

    # TODO get all git hashes?
    for j in jsons:
        strings = j['stringsFound']
        for s in strings:
            isblob = is_git_blob(s, j)
            if isblob is None:
                # TODO error
                raise RuntimeError("error", s)
            else:
                print(f"skipping {s}: {isblob}")

    res.check_returncode()
    # TODO


if __name__ == '__main__':
    main()
