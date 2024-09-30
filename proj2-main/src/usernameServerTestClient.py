import zmq
from time import time
from random import randint
import sys



context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://127.0.0.1:3459")

socket.send(("GET 2023/12/10 12:41:48").encode("utf-8"))

reply = socket.recv()

print(str(reply))