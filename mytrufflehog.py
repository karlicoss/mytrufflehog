#!/usr/bin/env python3
import argparse
from subprocess import run


def main():
    p = argparse.ArgumentParser()
    p.add_argument('rest', nargs=argparse.REMAINDER)
    args = p.parse_args()
    res = run([
        'trufflehog',
        '--json',
        # TODO no-json argument? would be nice to have a nice way of displaying...
        # TODO maybe, parse both?
        *args.rest,
    ])
    if res.returncode > 1:
        res.check_returncode()
    res.check_returncode()
    # TODO


if __name__ == '__main__':
    main()
