from ast import Sub
import time
import sys
from pubsubAPI import Subscriber

#sub_client.py id topic
args = sys.argv

if len(args) != 2:
    print("Numbers of arguments is not corret. Script is run as 'sub_client.py topic_name'.")
    sys.exit(0)

topic = args[1]
wait = False

sub = Subscriber()
#subscreve ao topico 
result = sub.subscribe(topic)
if result:
    print("Successfully subscribed to topic " + topic)
else:
    print("Failed to subscribe to topic "+ topic)

wait = True


while True:
    print("Retrieving messages...")
    messages = sub.get(topic)
    if messages != False:
        for message in messages:
            print("Received message: " +str(message))

    if wait:
        print("Waiting before next get...")
        time.sleep(3)
