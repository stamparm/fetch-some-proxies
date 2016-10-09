#!/usr/bin/env python

import json
import random
import re
import sys
import subprocess
import time
import urllib2

FALLBACK_METHOD = False
IFCONFIG_URL = "http://ifconfig.me"
PROXY_LIST_URL = "https://hidester.com/proxydata/php/data.php?mykey=csv&country=&port=&type=undefined&anonymity=undefined&ping=undefined&gproxy=2"
ROTATION_CHARS = ('/', '-', '\\', '|')
TIMEOUT = 10
USER_AGENT = "curl/7.22.0 (x86_64-pc-linux-gnu) libcurl/7.22.0 OpenSSL/1.0.1 zlib/1.2.3.4 libidn/1.23 librtmp/2.3"

def retrieve(url, data=None, headers={"User-agent": USER_AGENT}):
    try:
        req = urllib2.Request("".join(url[i].replace(' ', "%20") if i > url.find('?') else url[i] for i in xrange(len(url))), data, headers)
        retval = urllib2.urlopen(req, timeout=TIMEOUT).read()
    except Exception, ex:
        try:
            retval = ex.read() if hasattr(ex, "read") else getattr(ex, "msg", str())
        except:
            retval = None

    return retval or ""

process = subprocess.Popen("timeout %d curl %s" % (TIMEOUT, IFCONFIG_URL), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
stdout, _ = process.communicate()
FALLBACK_METHOD = re.search(r"\d+\.\d+\.\d+\.\d+", stdout or "") is None

counter = 0
proxies = json.loads(retrieve(PROXY_LIST_URL))
random.shuffle(proxies)

try:
    for proxy in proxies:
        result = ""
        counter += 1
        sys.stderr.write("\r%s\r" % ROTATION_CHARS[counter % len(ROTATION_CHARS)])
        sys.stderr.flush()
        start = time.time()
        candidate = "%s://%s:%s" % (proxy["type"], proxy["IP"], proxy["PORT"])
        if not FALLBACK_METHOD:
            process = subprocess.Popen("timeout %d curl --proxy %s %s" % (TIMEOUT, candidate, IFCONFIG_URL), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            result, _ = process.communicate()
        elif proxy["type"] in ("http", "https"):
            opener = urllib2.build_opener(urllib2.ProxyHandler({"http": candidate, "https": candidate}))
            urllib2.install_opener(opener)
            result = retrieve(IFCONFIG_URL)
        if (result or "").strip() == proxy["IP"].encode("utf8"):
            sys.stdout.write("\r%s" % candidate)
            sys.stdout.flush()
            sys.stderr.write("\t(latency: %.2fs; country: %s; anonimity: %s)" % (time.time() - start, proxy["country"].lower() or '-', proxy["anonymity"].lower() or '-'))
            sys.stderr.flush()
            sys.stdout.write("\n")
            sys.stdout.flush()
except KeyboardInterrupt:
    pass
