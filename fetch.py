#!/usr/bin/env python3
import platform
import click
import re
from config.clean import GetProxy
search = GetProxy()


@click.command()
@click.option('--anonymity','-an',default='high')
@click.option('--country','-c',default=None)
@click.option('--latency','-l',default=2)
@click.option('--output','-o',default=None)
@click.option('--thread','-t',default=4)
def main(**options):
    conn_params = {
            'anonymity': options.get('anonymity'),
            'country': options.get('country'),
            'latency': options.get('latency'),
            'output': options.get('output'),
            'thread': options.get('thread')
            }

    banner()
    search.run(**conn_params)
def banner():
    """ show me banner by use the re module and color"""
    if platform.system() != 'Windows':
        BANNER = re.sub(r"\|(\w)\|", lambda _: "|\033[01;41m%s\033[00;49m|" % _.group(1), GetProxy.BANNER)
        print(BANNER)

if __name__ == "__main__":
    main()

    
