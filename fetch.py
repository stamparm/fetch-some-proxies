#!/usr/bin/env python

import sys

if sys.version_info.major > 2:
    exit("[!] please run this program with Python v2.x")

import json
import os
import Queue
import random
import re
import string
import subprocess
import tempfile
import threading
import time
import urllib2

VERSION = "2.1"
BANNER = """
+-++-++-++-++-++-++-++-++-++-++-++-++-++-++-++-++-++-+
|f||e||t||c||h||-||s||o||m||e||-||p||r||o||x||i||e||s| <- v%s
+-++-++-++-++-++-++-++-++-++-++-++-++-++-++-++-++-++-+""".strip("\r\n") % VERSION
FALLBACK_METHOD = False
IFCONFIG_URL = "http://ipecho.net/plain"
PROXY_LIST_URL = "https://hidester.com/proxydata/php/data.php?mykey=csv&gproxy=2"
ROTATION_CHARS = ('/', '-', '\\', '|')
TIMEOUT = 10
THREADS = 10
USER_AGENT = "curl/7.{curl_minor}.{curl_revision} (x86_64-pc-linux-gnu) libcurl/7.{curl_minor}.{curl_revision} OpenSSL/0.9.8{openssl_revision} zlib/1.2.{zlib_revision}".format(curl_minor=random.randint(8, 22), curl_revision=random.randint(1, 9), openssl_revision=random.choice(string.lowercase), zlib_revision=random.randint(2, 6))
ANONIMITY_LEVELS = {"elite": "high", "anonymous": "medium", "transparent": "low"}

if not subprocess.mswindows:
    BANNER = re.sub(r"\|(\w)\|", lambda _: "|\033[01;41m%s\033[00;49m|" % _.group(1), BANNER)

counter = [0]
threads = []

def retrieve(url, data=None, headers={"User-agent": USER_AGENT}):
    try:
        req = urllib2.Request("".join(url[i].replace(' ', "%20") if i > url.find('?') else url[i] for i in xrange(len(url))), data, headers)
        retval = urllib2.urlopen(req, timeout=TIMEOUT).read()
    except Exception as ex:
        try:
            retval = ex.read() if hasattr(ex, "read") else getattr(ex, "msg", str())
        except:
            retval = None

    return retval or ""

def worker(queue, handle=None):
    try:
        while True:
            proxy = queue.get_nowait()
            result = ""
            counter[0] += 1
            sys.stdout.write("\r%s\r" % ROTATION_CHARS[counter[0] % len(ROTATION_CHARS)])
            sys.stdout.flush()
            start = time.time()
            candidate = "%s://%s:%s" % (proxy["type"], proxy["IP"], proxy["PORT"])
            if not all((proxy["IP"], proxy["PORT"])) or re.search(r"[^:/\w.]", candidate):
                continue
            if not FALLBACK_METHOD:
                process = subprocess.Popen("curl -m %d -A '%s' --proxy %s %s" % (TIMEOUT, USER_AGENT, candidate, IFCONFIG_URL), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                result, _ = process.communicate()
            elif proxy["type"] in ("http", "https"):
                opener = urllib2.build_opener(urllib2.ProxyHandler({"http": candidate, "https": candidate}))
                urllib2.install_opener(opener)
                result = retrieve(IFCONFIG_URL)
            if (result or "").strip() == proxy["IP"].encode("utf8"):
                latency = time.time() - start
                if latency < TIMEOUT:
                    if handle:
                        handle.write("%s%s" % (candidate, os.linesep))
                        handle.flush()
                    sys.stdout.write("\r%s%s # latency: %.2f sec; country: %s; anonimity: %s (%s)\n" % (candidate, " " * (32 - len(candidate)), latency, ' '.join(_.capitalize() for _ in (proxy["country"].lower() or '-').split(' ')), proxy["anonymity"].lower() or '-', ANONIMITY_LEVELS.get(proxy["anonymity"].lower(), '-')))
                    sys.stdout.flush()
    except Queue.Empty:
        pass

def main():
    global FALLBACK_METHOD

    sys.stdout.write("%s\n\n" % BANNER)
    sys.stdout.write("[i] initial testing...\n")

    process = subprocess.Popen("curl -m %d -A '%s' %s" % (TIMEOUT, USER_AGENT, IFCONFIG_URL), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, _ = process.communicate()
    FALLBACK_METHOD = re.search(r"\d+\.\d+\.\d+\.\d+", stdout or "") is None

    sys.stdout.write("[i] retrieving list of proxies...\n")
    try:
        proxies = json.loads(retrieve(PROXY_LIST_URL))
    except:
        exit("[!] something went wrong during the proxy list retrieval/parsing. Please check your network settings and try again")
    random.shuffle(proxies)

    _, filepath = tempfile.mkstemp(prefix="proxies", suffix=".txt")
    os.close(_)
    handle = open(filepath, "w+b")

    sys.stdout.write("[i] storing results to '%s'...\n" % filepath)

    queue = Queue.Queue()
    for proxy in proxies:
        queue.put(proxy)

    sys.stdout.write("[i] testing %d proxies (%d threads)...\n\n" % (len(proxies), THREADS))
    for _ in xrange(THREADS):
        thread = threading.Thread(target=worker, args=[queue, handle])
        thread.daemon = True

        try:
            thread.start()
        except ThreadError as ex:
            sys.stderr.write("[x] error occurred while starting new thread ('%s')" % ex.message)
            break

        threads.append(thread)

    try:
        alive = True
        while alive:
            alive = False
            for thread in threads:
                if thread.isAlive():
                    alive = True
                    time.sleep(0.1)
    except KeyboardInterrupt:
        sys.stderr.write("\r   \n[!] Ctrl-C pressed\n")
    else:
        sys.stdout.write("\n[i] done\n")
    finally:
        sys.stdout.flush()
        sys.stderr.flush()
        handle.flush()
        handle.close()

if __name__ == "__main__":
    main()