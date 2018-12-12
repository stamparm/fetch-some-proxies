from abc import ABCMeta,abstractmethod
import random
import string
class Fields(metaclass=ABCMeta):
    ###########################################################################
    VERSION = "3.0.3"
    BANNER = """
    +-++-++-++-++-++-++-++-++-++-++-++-++-++-++-++-++-++-+
    |f||e||t||c||h||-||s||o||m||e||-||p||r||o||x||i||e||s| <--v%s
    +-++-++-++-++-++-++-++-++-++-++-++-++-++-++-++-++-++-+""".strip("\r\n") %VERSION
    #level proxy
    ANONYMITY_LEVELS = {'high':'elite',"medium":'anonymous','low':"transparent"}
    FALLBAK_METHOD = False
    #show public Ip
    IFCONFIG_CANDIDATES = ("https://ifconfig.co/ip","https://api.ipify.org/?format=text",
                        "https://ifconfig.io/ip","https://myexternalip.com/raw",
                        "https://wtfismyip.com/text","https://icanhazip.com",
                        "https://ipv4bot.whatismyipaddress.com","https://ipv4.seeip.org")
    IFCONFIG_URL = None
    MAX_HELP_OPTION_LENGTH = 18
    PROXY_LIST_URL = "https://raw.githubusercontent.com/stamparm/aux/master/fetch-some-list.txt"
    ROTATION_CHARS = ('/','-','\\','|')
    TIMEOUT = 10
    THREADS = 10
    #################################################################################################3
    #SET USER_AGENT
    USER_AGENT = """culr/7.{curl_minor}.{curl_revision} (x86_64-pc-linux-gnu) libcurl/7.{curl_minor}
                .{curl_revision} openSSL/0.9.8{openssl_revision} zlib/1.2.{zlib_revision}""".format(
                        curl_minor=random.randint(8,22),curl_revision=random.randint(1,9),
                        openssl_revision=random.choice(string.ascii_lowercase),
                        zlib_revision=random.randint(2,6))
    ##############################################################################################
    options = None
    counter = [0]
    threads = []
    ###############################################

    
    @abstractmethod
    def _retrieve():
        pass
    @abstractmethod
    def _worker():
        pass
    @abstractmethod
    def run():
        pass
    @abstractmethod
    def main(cls):
        pass


        






if __name__ == "__main__":
    
    print (subprocess)
    


