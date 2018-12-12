#!/usr/bin/env python
from config.module import *
from config.fields import Fields
from fake_useragent import UserAgent
name = UserAgent() 
from functools import wraps
class GetProxy(Fields):
    LATENCY = 5


    def _retrieve(self, url:str=Fields.PROXY_LIST_URL, proxies:str=None)->str:
        '''if you want replace space encoding use this code if you want'''
        """
            ''.join(name[i].replace(' ',"=",) if (i > name.find('?')
            and i == int(name.find('?')) +1 or '') else
            ...:  name[i] for i in range(len(name)))
        """
        """
            :parm url url for search
            :param proxies for set proxies
        """
        if proxies:
            result = requests.get(url, proxies, headers={'User-Agent': name.random}, timeout=5).text
        else:
            result = requests.get(url, headers={'User-Agent': name.random}, timeout=5).json()
        return result
        

    
    def _worker(self, queue1: queue=None, latency: int=None, output: str=None)->str:
        """
            :parm queue1 set object queue 
            :parm latency for set time for bether proxy time
            :parm output for set output for write proxy in the file
        """
        
        try:
            while True:
                #Equivalent to get(False)
                proxy = queue1.get_nowait()
                result = ""
                """ for progress bar test by %"""
                GetProxy.counter[0] += 1
                sys.stdout.write("\r%s\r"
                                 %Fields.ROTATION_CHARS[Fields.counter[0]
                                                        % len(Fields.ROTATION_CHARS)])
                sys.stdout.flush()
                start = time.time()
                candidate = "%s://%s:%s" %(proxy['proto'].replace('http', 'https'),
                                           proxy["ip"], proxy["port"])
                if 'https' in candidate:
                    if platform.system() == 'Linux':
                        process = subprocess.Popen("curl -m %d -A \"%s\" --proxy %s %s"
                                                   % (Fields.TIMEOUT, Fields.USER_AGENT, candidate,
                                                      Fields.IFCONFIG_CANDIDATES[4]), shell=True,
                                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        result, _ = process.communicate()
                    elif platform.system() == 'Windows':
                        try:
                            result = requests.get(Fields.IFCONFIG_CANDIDATES[4],
                                                  proxies={'https':candidate}, timeout=5).text
                        except:
                            continue
                        else:
                        
                            result=result.strip().encode()
                """if 'socks' in candidate:
                    try:


                        result = requests.get(Fields.IFCONFIG_CANDIDATES[4],
                                proxies={'https':candidate,'http':candidate}, timeout=5).text
                    except:
                        continue"""
                    
                    
                if ((getattr(result, 'encode', '') or
                     getattr(result, 'decode', ''))().strip() == proxy['ip']):
                    latency1 = time.time() -start
                    if(latency1 <= latency or GetProxy.LATENCY):
                        sys.stdout.write("\r%s%s # latency: %.2f sec; country:"
                                         "%s; anonymity:%s (%s)\n"
                                         %(candidate, " " * (32 - len(candidate)),
                                                             latency, ' '.join(
                                                   _.capitalize()
                                                   for _ in (proxy['country'].lower()
                                                             or '-').split(' ')),
                                               proxy["type"], proxy["anonymity"]))
                        sys.stdout.flush()
                        if output:
                            with open(output, 'a') as free:
                                free.write(candidate + os.linesep)
        except queue.Empty:
            pass
    def run(self, **options:dict)->queue:
        """
            :parm output for set name file
            :parm latency for set time proxy
            :parm anonymity for anonymity
            :parm country for set country
            :parm thread for set thread
        """

        print("[!] initi testing....")
        GetProxy.LATENCY = options['latency']
        self.queue1 = queue.Queue()
        proxies = self._retrieve()
        if type(proxies) == str:
            print(type(proxies))
        else:
            if options:
                for proxy in proxies:
                    if proxy['anonymity'] in options['anonymity']:
                        if options['country']:
                            if proxy['country'].lower() in options['country']:
                                self.queue1.put(proxy)
                        else:
                            self.queue1.put(proxy)
                for _ in range(options['thread'] or GetProxy.THREADS):
                    thread = threading.Thread(target=self._worker,
                                              args=(self.queue1, options['latency'],
                                                    options['output']))
                    thread.daemon = True
                    thread.start()
                    GetProxy.threads.append(thread)
                print("number thread for test is %d"%(len(GetProxy.threads)))
                print("number proxy for test %d"%(self.queue1.qsize()))

            try:
                alive = True
                while alive:
                    alive = False
                    for thread in GetProxy.threads:
                        if thread.is_alive():
                            alive = True
                            time.sleep(0.1)
            except KeyboardInterrupt:
                sys.stderr.write("\r   \n[!] Ctrl-C pressed\n")
            else:
                sys.stdout.write("\n[!] done\n")
            finally:
                sys.stdout.flush()
                sys.stderr.flush()
    @classmethod
    def main(cls):
        pass

if __name__ == '__main__':
    name = GetProxy()
    name.run()
