import string    
import random
import time
import zmq
import sys
import signal
from pubsubAPI import Publisher

# Signal Handler for Ctrl+C
def signal_handler(sig, frame):
    print('Closing Publisher!')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


# Script is run "publisher.py topic total_puts"
args = sys.argv

if len(args) !=2:
    print("Numbers of arguments is not corret. Script is run as 'publisher.py topic_name'.")
    sys.exit(0)

topic = args[1]
    
pub = Publisher(topic)

wait = False

while True:
    try:
        a = input("Put: ")
        result = pub.put(a)
        if result == True:
            print("Put successfully")
        else:
            print("Failed to put message")
    except KeyboardInterrupt:
        break
    
