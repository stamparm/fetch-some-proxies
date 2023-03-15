#!/usr/bin/env python
import json
import optparse
import os
import random
import re
import socket
import subprocess
import sys
import threading
import time
import urllib
import queue
import urllib.request
from typing import Optional

build_opener = urllib.request.build_opener
install_opener = urllib.request.install_opener
quote = urllib.parse.quote
urlopen = urllib.request.urlopen
ProxyHandler = urllib.request.ProxyHandler
Queue = queue.Queue
Request = urllib.request.Request

xrange = range


VERSION: str = "3.2.4"
BANNER: str = """
+-++-++-++-++-++-++-++-++-++-++-++-++-++-++-++-++-++-+
|f||e||t||c||h||-||s||o||m||e||-||p||r||o||x||i||e||s| <- v%s
+-++-++-++-++-++-++-++-++-++-++-++-++-++-++-++-++-++-+""".strip("\r\n") % VERSION

ANONIMITY_LEVELS: dict[str, str] = {"high": "elite", "medium": "anonymous", "low": "transparent"}
FALLBACK_METHOD: bool = False
IFCONFIG_CANDIDATES: tuple[str, ...] = ("https://api.ipify.org/?format=text", "https://myexternalip.com/raw", "https://wtfismyip.com/text", "https://icanhazip.com/", "https://ip4.seeip.org")
IS_WIN: bool = os.name == "nt"
MAX_HELP_OPTION_LENGTH: int = 18
PROXY_LIST_URL: str = "https://raw.githubusercontent.com/stamparm/aux/master/fetch-some-list.txt"
ROTATION_CHARS: tuple[str, ...] = ('/', '-', '\\', '|')
TIMEOUT: int = 10
THREADS: int = 20
USER_AGENT: str = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:88.0) Gecko/20100101 Firefox/88.0"

if not IS_WIN:
    BANNER = re.sub(r"\|(\w)\|", lambda _: "|\033[01;41m%s\033[00;49m|" % _.group(1), BANNER)

options: None = None
counter: list[int] = [0]
threads: list[int] = []
timeout: int = TIMEOUT

def check_alive(address: str, port: int) -> bool:
    result: bool  = False

    try:
        s: socket = socket.socket()
        s.connect((address, port))
        result = True
    except:
        pass
    finally:
        try:
            s.shutdown(socket.SHUT_RDWR)
            s.close()
        except:
            pass

    return result

def retrieve(
    url: str, 
    data: Optional[bytes] = None, 
    headers: Optional[dict[str, str]] = {"User-agent": USER_AGENT}, 
    timeout: Optional[int] = timeout, 
    opener: Optional[object] = None
) -> str:
    try:
        req: Request = Request("".join(url[i].replace(' ', "%20") if i > url.find('?') else url[i] for i in range(len(url))), data, headers)
        retval = (urlopen if not opener else opener.open)(req, timeout=timeout).read()
    except Exception as ex:
        try:
            retval: str = ex.read() if hasattr(ex, "read") else getattr(ex, "msg", str())
        except:
            retval = None

    return (retval or b"").decode("utf8")

def worker(queue: Queue, handle: Optional[int] = None) -> None:
    try:
        while True:
            proxy = queue.get_nowait()
            result: str = ""
            counter[0] += 1
            sys.stdout.write("\r%s\r" % ROTATION_CHARS[counter[0] % len(ROTATION_CHARS)])
            sys.stdout.flush()
            start: float = time.time()
            candidate: str = "%s://%s:%s" % (proxy["proto"].replace("https", "http"), proxy["ip"], proxy["port"])
            if not all((proxy["ip"], proxy["port"])) or re.search(r"[^:/\w.]", candidate):
                continue
            if not check_alive(proxy["ip"], proxy["port"]):
                continue
            if not FALLBACK_METHOD:
                process: Popen[bytes] = subprocess.Popen("curl -m %d -A \"%s\" --proxy %s %s" % (timeout, USER_AGENT, candidate, random_ifconfig()), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                result, _ = process.communicate()
            elif proxy["proto"] in ("http", "https"):
                opener: OpenerDirector = build_opener(ProxyHandler({"http": candidate, "https": candidate}))
                result = retrieve(random_ifconfig(), timeout=timeout, opener=opener)
            if (result or "").strip() == proxy["ip"].encode("utf8"):
                latency: float = time.time() - start
                if latency < timeout:
                    sys.stdout.write("\r%s%s # latency: %.2f sec; country: %s; anonymity: %s (%s)\n" % (candidate, " " * (32 - len(candidate)), latency, ' '.join(_.capitalize() for _ in (proxy["country"].lower() or '-').split(' ')), proxy["type"], proxy["anonymity"]))
                    sys.stdout.flush()
                    if handle:
                        os.write(handle, ("%s%s" % (candidate, os.linesep)).encode("utf8"))
    except:
        pass
    
def random_ifconfig() -> str:
    retval: str = random.sample(IFCONFIG_CANDIDATES, 1)[0]

    if options.noHttps:
        retval = retval.replace("https://", "http://")

    return retval

def run():
    global FALLBACK_METHOD
    global timeout

    sys.stdout.write("[i] initial testing...\n")

    timeout = min(options.timeout or sys.maxsize, options.maxLatency or sys.maxsize, TIMEOUT)
    socket.setdefaulttimeout(timeout)

    process: Popen[bytes] = subprocess.Popen("curl -m %d -A \"%s\" %s" % (TIMEOUT, USER_AGENT, random_ifconfig()), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    FALLBACK_METHOD = re.search(r"\d+\.\d+\.\d+\.\d+", (stdout or b"").decode("utf8")) is None

    if stderr and any(_ in stderr for _ in (b"not found", b"not recognized")):
        sys.stdout.write("[x] command 'curl' not available\n")

    sys.stdout.write("[i] retrieving list of proxies...\n")
    content = retrieve(PROXY_LIST_URL, headers={"User-agent": USER_AGENT})
    if not all(_ in content for _ in ("proto", "country", "anonymity")):
        exit("[!] something went wrong during the proxy list retrieval/parsing ('%s'). Please check your network settings and try again" % content[:100])

    proxies = json.loads(content)
    random.shuffle(proxies)

    if any((options.country, options.anonymity, options.type, options.port)):
        _: list = []

        if options.port:
            options.port = set(int(_) for _ in re.findall(r"\d+", options.port))

        for proxy in proxies:
            if options.country and not re.search(options.country, proxy["country"], re.I):
                continue
            if options.port and not proxy["port"] in options.port:
                continue
            if options.anonymity and not re.search(options.anonymity, "%s (%s)" % (proxy["anonymity"], ANONIMITY_LEVELS.get(proxy["anonymity"].lower(), "")), re.I):
                continue
            if options.type and not re.search(options.type, proxy["proto"], re.I):
                continue
            _.append(proxy)
        proxies: list = _

    if options.outputFile:
        handle: int = os.open(options.outputFile, os.O_APPEND | os.O_CREAT | os.O_TRUNC | os.O_WRONLY)
        sys.stdout.write("[i] storing results to '%s'...\n" % options.outputFile)
    else:
        handle = None

    queue = Queue()
    for proxy in proxies:
        queue.put(proxy)

    if len(proxies) == 0:
        exit("[!] no proxies found")

    sys.stdout.write("[i] testing %d proxies (%d threads)...\n\n" % (len(proxies) if not FALLBACK_METHOD else sum(proxy["proto"] in ("http", "https") for proxy in proxies), options.threads or THREADS))
    for _ in xrange(options.threads or THREADS):
        thread = threading.Thread(target=worker, args=[queue, handle])
        thread.daemon = True

        try:
            thread.start()
        except threading.ThreadError as ex:
            sys.stderr.write("[x] error occurred while starting new thread ('%s')" % ex.message)
            break

        threads.append(thread)

    try:
        alive: bool = True
        while alive:
            alive = False
            for thread in threads:
                if thread.is_alive():
                    alive = True
                    time.sleep(0.1)
    except KeyboardInterrupt:
        sys.stderr.write("\r   \n[!] Ctrl-C pressed\n")
    else:
        sys.stdout.write("\n[i] done\n")
    finally:
        sys.stdout.flush()
        sys.stderr.flush()
        if handle:
            os.close(handle)
        os._exit(0)

def main():
    global options

    if "--raw" in sys.argv:
        sys._stdout = sys.stdout

        class _:
            def write(self, value) -> None:
                if "//" in value:
                    sys._stdout.write("%s\n" % value.split()[0])

            def flush(self) -> None:
                sys._stdout.flush()

        sys.stderr = sys.stdout = _()

    sys.stdout.write("%s\n\n" % BANNER)
    parser = optparse.OptionParser(version=VERSION)
    parser.add_option("--anonymity", dest="anonymity", help="Regex for filtering anonymity (e.g. \"anonymous|elite\")")
    parser.add_option("--country", dest="country", help="Regex for filtering country (e.g. \"china|brazil\")")
    parser.add_option("--max-latency", dest="maxLatency", type=float, help="Maximum (tolerable) latency in seconds (default %d)" % TIMEOUT)
    parser.add_option("--no-https", dest="noHttps", action="store_true", help="Disable HTTPS checking (not recommended)")
    parser.add_option("--output", dest="outputFile", help="Store resulting proxies to output file")
    parser.add_option("--port", dest="port", help="List of ports for filtering (e.g. \"1080,8000\")")
    parser.add_option("--raw", dest="raw", action="store_false", help="Display only results (minimal verbosity)")
    parser.add_option("--threads", dest="threads", type=int, help="Number of scanning threads (default %d)" % THREADS)
    parser.add_option("--timeout", dest="timeout", type=int, help="Request timeout in seconds (default %d)" % TIMEOUT)
    parser.add_option("--type", dest="type", help="Regex for filtering proxy type (e.g. \"http\")")

    # Dirty hack(s) for help message
    def _(self, *args):
        retval = parser.formatter._format_option_strings(*args)
        if len(retval) > MAX_HELP_OPTION_LENGTH:
            retval = ("%%.%ds.." % (MAX_HELP_OPTION_LENGTH - parser.formatter.indent_increment)) % retval
        return retval

    parser.formatter._format_option_strings = parser.formatter.format_option_strings
    parser.formatter.format_option_strings = type(parser.formatter.format_option_strings)(_, parser)

    for _ in ("-h", "--version"):
        option = parser.get_option(_)
        option.help = option.help.capitalize()

    try:
        options, _ = parser.parse_args()
    except SystemExit:
        sys.stdout.write("\n")
        sys.stdout.flush()
        raise

    run()

if __name__ == "__main__":
    main()
