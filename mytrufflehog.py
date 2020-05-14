#!/usr/bin/env python3
import argparse
from pathlib import Path
import re
import sys
import json
from subprocess import run, PIPE
from typing import Optional, Set


from kython.klogging2 import LazyLogger

logger = LazyLogger('mytrufflehog', level='info')


Reason = str

# TODO ugh. need to test it properly...

BLOB_RE = r'https?://github.com     /\w+/\w+/blob/               [0-9a-z]{40}(/[\w\.]+)*'
PULL_RE = r'https?://github.com     /\w+/\w+/pull/[0-9]+/commits/[0-9a-z]{40}'
GIST_RE = r'https?://gist.github.com/\w+/         [0-9a-z]{32}(/[\w\.]+)*'

RES = [re.compile(x, re.VERBOSE) for x in (BLOB_RE, PULL_RE, GIST_RE)]


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
        for RE in RES:
            for m in re.finditer(RE, line):
                (fr, to) = m.span()
                if fr <= occurence < to:
                    return f'Occuring in: {line}'
    return None


def print_report(jsons):
    for j in jsons:
        header = f'''
Reason: {j['reason']}
Date: {j['date']}
Hash: {j['commitHash']}
Filepath: {j['path']}
Branch: {j['branch']}
Commit: {j['commit']}
'''
        print('\033[32m' + header + '\033[0m')
        print(j['printDiff']) # already coloured


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

    logged: Set[str] = set()
    def log_once(s: str, reason: str):
        if s in logged:
            return
        logged.add(s)
        logger.info('skipping %s', s)
        logger.debug('reason: %s', reason)

    filtered_jsons = []
    # TODO get all git hashes?
    for j in jsons:
        strings = j['stringsFound']
        filtered_strings = []
        for s in set(strings): # sometimes there are duplicates..
            isblob = is_git_blob(s, j)
            if isblob is None:
                filtered_strings.append(s)
            else:
                log_once(s, isblob)

        if len(filtered_strings) > 0:
            j['stringsFound'] = filtered_strings
            filtered_jsons.append(j)

    if len(filtered_jsons) == 0:
        sys.exit(0)

    print_report(filtered_jsons)
    sys.exit(1)


if __name__ == '__main__':
    main()
