import signal
import sys
from pubsubAPI import Proxy

# Script is run "proxy.py time_between_save"
print("Starting proxy")
proxy = Proxy()
proxy.run()