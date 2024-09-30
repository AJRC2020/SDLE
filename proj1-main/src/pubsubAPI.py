from concurrent.futures.process import _MAX_WINDOWS_WORKERS
from email import message
from matplotlib.pyplot import flag
import zmq
import re
from time import time
import sys

TIMEOUT = 3


#Messages cannot have the ':' character, therefore it is substituted by ':/'
def encodeMessages(messageArray):
    encodedResult = ""
    for message in messageArray:
        if(type(message) != str):
            print("Failed to encode message because it is not a string")
            return None
        encodedMessage = message.replace(':','::')
        encodedResult += encodedMessage + ":/"
    encodedResult = encodedResult[:-2]
    return encodedResult

#Reverse process of the encodeMessage function
def decodeMessage(encodedMessage):
    if(type(encodedMessage) != str):
        print("Failed to encode message because it is not a string")
        return None
    encodedParts = encodedMessage.split(':/')
    decodedMessages = []
    for encodedPart in encodedParts:
        decodedMessages.append(encodedPart.replace("::",":"))
    return decodedMessages

class Subscriber:
    ip = "127.0.0.1"
    port = "5556"
    def __init__(self, ip=ip, port=port) -> None:
        print("Creating subscriber")
        self.ip = ip
        self.port = port
        context = zmq.Context()
        self.proxy_socket = context.socket(zmq.REQ)
        self.proxy_socket.connect('tcp://' + ip + ':' + port)
        if self.proxy_socket == None:
            print("Failed to connect subscriber to proxy")
            return None
        print("Connected subscriber to proxy")
        #Get ID from proxy
        self.proxy_socket.send("LOGIN".encode('utf-8'))
        requestStartTime = time()
        reply = None
        print("Sent LOGIN to proxy")
        while time() - requestStartTime < TIMEOUT and reply == None:
            reply = self.proxy_socket.recv()
        if reply == None:
            print("Failed to connect to proxy")
            return None
        #A reply e do tipo "LOGIN:<userid>"
        self.id= int(reply[6:])
        print("My id is "+ str(self.id))
        self.lastReceivedMessageID = {} #Representa pares entre nomes de topicos ao qual o subscriber ta subscrito e a ultima mensagem que recebeu desse topico para garantir que nao a mesnagens duplicadas
     
        
    def get(self, topic):
            get_msg = "GET " + str(self.id) + " " + topic
            self.proxy_socket.send(get_msg.encode('utf-8'))
            #Try to receive message until timeout
            reply = None
            requestStartTime = time()
            while (time() - requestStartTime) < TIMEOUT and reply == None:
                reply = self.proxy_socket.recv()
            reply = reply.decode('utf-8')
            if reply == None:
                print("Failed to get data from topic "  + topic)
                self.sendNACK()
                self.proxy_socket.close()
                return False
            #nao esta subscrito
            if reply == "NOT_SUBSCRIBED":
                print("Client is not subscribed to topic " + topic)
                #self.sendNACK() Two-way-handshake deve ser suficiente
                return False
            #topic nao existen e nome invalido
            elif reply == "INVALID_TOPIC":
                print("Topic does not exist yet and the name is not valid")
                #self.sendNACK()
                return False
            elif reply == "NO_MESSAGES":
                print("There are no new messages at the moment.")
                return False
            #topico existe e nome valido
            else:
                receivedMessages = decodeMessage(reply) #decodes a received message into an array of message_id:message
                messagesToReturn = []
                messageIDsToAck = []
                for message in receivedMessages:
                    separator = message.find(":")
                    messageID  =  int(message[:separator])
                    if topic not in self.lastReceivedMessageID.keys():
                        #Topic did not yet have a record oon the acknowledgments registrations
                        self.lastReceivedMessageID[topic] = messageID
                        messagesToReturn.append(message[separator+1:])
                        self.lastReceivedMessageID[topic]=messageID
                        messageIDsToAck.append(messageID)
                    elif messageID > self.lastReceivedMessageID[topic]:
                        #Message Valid and going to be returned
                        self.lastReceivedMessageID[topic] = messageID
                        messagesToReturn.append(message[separator+1:])
                        self.lastReceivedMessageID[topic]=messageID
                        messageIDsToAck.append(messageID)
                    else:
                        #Message received before
                        print("Duplicate method received")
                        messageIDsToAck.append(messageID)
                self.sendACK(messageIDsToAck,topic)
                if len(messagesToReturn) == 0:
                    return False
                else:
                    return messagesToReturn


    def subscribe(self, topic):
        subs_msg = "SUB " + str(self.id) + " " + topic
        self.proxy_socket.send(subs_msg.encode('utf-8'))

        requestStartTime = time()
        reply = None
        while time() - requestStartTime < TIMEOUT and reply == None:
            reply = self.proxy_socket.recv()

        if reply == None:
            print("Failed to subscribe topic " + topic)
            self.proxy_socket.close()
            return False
        return True


    
    def unsubscribe(self, topic):
        unsub_msg = "UNSUB " + str(self.id) + " " + topic
        self.proxy_socket.send(unsub_msg.encode('utf-8'))
        
        reply = self.proxy_socket.recv()

        if reply == None:
            print("Failed to subscribe topic " + topic)
            self.proxy_socket.close()
            return False
        elif reply == "NON_EXISTENT":
            print("The topic" + topic + " does not exist")
            return False
        return True

    def sendACK(self,messages_ids, topic):
        message = "ACK " + str(self.id) + " " + topic + " "
        for id in messages_ids:
            message+= str(id) + ","
        message = message[:-1]
        self.proxy_socket.send(message.encode('utf-8'))
        
        reply = self.proxy_socket.recv()

        if reply == None:
            print("Failed to reset state")
            self.proxy_socket.close()
            return False
        else:
            return True
    def sendNACK(self):
        self.proxy_socket.snd("NACK".encode('utf-8'))

        
    


class Publisher:
    ip = "127.0.0.1"
    port = "5555"
    def __init__(self, topic, ip=ip, port=port) -> None:
        self.ip = ip
        self.port = port
        self.topic = topic
        context = zmq.Context()
        self.proxy_socket = context.socket(zmq.REQ)
        self.proxy_socket.connect("tcp://" + ip + ":" + port)

    #Puts message in topic. Returns true if message put successfully and false if not
    def put(self, message):
        put_msg = "PUT " + self.topic + " " + message

        self.proxy_socket.send(put_msg.encode('utf-8'))
        print("Sent: " + put_msg)
        #To do todo: Talvez adicionar timeout
        reply = self.proxy_socket.recv().decode('utf-8')

        if reply == None:
            print("Failed to put data in topic "  + self.topic)
            self.proxy_socket.close()
            return False
        elif reply == "NON_EXISTENT":
            print("Failed to put data in topic " + self.topic + " because topic does not exist")
            return False
        if reply == "ACK":
            return True
        else:
            return False


#   SUB     SUB     SUB     SUB 
#    |       |       |       |
#    +-------+---+---+-------+
#                |
#      +---------+----------+
#      | subscribers_scoket |
#      |      PROXY         |
#      |  publishers_socket |
#      +---------+----------+
#                |
#    +-------+---+---+-------+
#    |       |       |       |
#   PUB     PUB     PUB     PUB

class Proxy:
    publishers_port = "5555"
    subscribers_port = "5556"
    ip = "127.0.0.1"
    topics = {}   
    def __init__(self, publisher_port=publishers_port, subscribers_port=subscribers_port, ip=ip) -> None:
        self.publisher_context = zmq.Context()
        self.publisher_socket = self.publisher_context.socket(zmq.REP)
        self.publisher_socket.bind("tcp://" + ip + ":" + publisher_port)

        self.subscribers_context = zmq.Context()
        self.subscribers_socket = self.subscribers_context.socket(zmq.REP)
        self.subscribers_socket.bind("tcp://" + ip + ":" + subscribers_port)

        self.poller = zmq.Poller()
        self.poller.register(self.subscribers_socket, zmq.POLLIN)
        self.poller.register(self.publisher_socket, zmq.POLLIN)
        self.lastConnectedUserID = 0
    """
    def hello_message(sub_id, topic):
        if topic not in topics.keys:
            top = Topic(topic)
            top.subscribe(sub_id)
            topics[topic] = Topic(topic)

        else:
            topics[topic].subscribe(sub_id)

        self.frontend.send("hello".encode('utf-8'))

    def goodbye_message(sub_id, topic):
        topics[topic].unsubscribe(sub_id)
        self.frontend.send("goodbye".encode('utf-8'))
    """

    def run(self):
        print("Proxy started")
        exit = False
        while not exit:
            event = dict(self.poller.poll())
            if self.publisher_socket in event:
                request = self.publisher_socket.recv()
            elif self.subscribers_socket in event:
                request = self.subscribers_socket.recv()
            else:
                print("Message to receive from unknown socket")
                print(event)
            if type(request) != str:
                request = request.decode('utf-8')
            print("Received request: " + request)
            command = ""
            if (request.find(' ') != -1):
                command = request[0:request.find(' ')]
            else:
                command = request
            if command == "SUB":
                print("Received subscription")
                if request.find(" ") == -1:
                    print("Invalid request received! (" + request + ")")
                    continue
                lastIndex = 4
                subID = request[lastIndex:request.find(' ',lastIndex)] 
                lastIndex += len(subID) + 1
                topicName = request[lastIndex:]
                #verifica se nome do topico tem espaços
                if bool(re.search(r"\s", topicName)):
                    #atualizar nome do tópico 
                    topicName = topicName.replace(" ", "_")
                #se topico não existe, cria um novo
                if (topicName not in self.topics.keys()):
                    self.topics[topicName] = Topic(topicName)
                #adicionar subscriber à lista de subscriber do topico
                self.topics[topicName].subscribers.append(subID) 
                self.subscribers_socket.send_string("ACK_SUB")
                print("Subscriber " + str(subID) + " subscribed to topic " + topicName + ". Sending acknowledgment")
                
            if command == "UNSUB":
                print("Received unsubscription")
                if request.find(" ") == -1:
                    print("Invalid request received! (" + request + ")")
                    continue
                req_list = request.split(" ") # 1 = sub_id 2 = topic
                #verificar se o topico existe
                if req_list[2] not in self.topics.keys():
                    print("Topic doesnt exist!")
                    self.subscribers_socket.send("NON_EXISTENTENT".encode('utf-8'))
                #dar unsubscribe do cliente desse topico
                else:
                    self.topics[req_list[2]].unsubscribe(req_list[1])
                    self.subscribers_socket.send("SUCCESS".encode('utf-8')) 
                
            if command == "GET":
                if request.find(" ") == -1:
                    print("Invalid request received! (" + request + ")")
                    continue
                topicInfo = request.split(" ")
                subID = topicInfo[1]                
                #Check se topico existe
                if topicInfo[2] not in self.topics.keys():
                    print("Topic " + topicInfo[2] + " doesn't exist!") 
                    self.subscribers_context.send("NON_EXISTENT".encode('utf-8')) #subscriber
                    continue
                #Check se esta subscrito
                elif subID not in self.topics[topicInfo[2]].subscribers:
                    print("User " + subID + " not subscribed to the topic " + topicInfo[2] + "! (" + str(self.topics[topicInfo[2]].subscribers) + ")")
                    self.subscribers_context.send("NOT_SUBSCRIBED".encode('utf-8')) #subscriber
                    continue
                
                #Percorrer a Lista
                messagesToSend = []
                messageCount = 0
                for message in self.topics[topicInfo[2]].messages:
                    #Checks if sub hasn't received it
                    if subID in message.subscribersLeft:
                        messagesToSend.append(message.messageID + ":" + message.text)
                        messageCount += 1
                #Enviar Lista
                if messageCount == 0:
                    self.subscribers_socket.send("NO_MESSAGES".encode('utf-8'))
                    print("No messages to send")
                else:
                    self.subscribers_socket.send(encodeMessages(messagesToSend).encode('utf-8'))
                    print("Sent " + str(messageCount) + " messages")
                    
            if command == "LOGIN":
                print("Received login attempt")
                self.lastConnectedUserID +=1
                print("Replying with " + "LOGIN:"+str(self.lastConnectedUserID))
                self.subscribers_socket.send_string("LOGIN:"+str(self.lastConnectedUserID))
                
                    
                    
                
            if command == "PUT":
                
                if request.find(" ") == -1:
                    print("Invalid request received! (" + request + ")")
                    continue
                lastIndex = 4
                #publisherID = request[lastIndex:request.find(' ',lastIndex)]
                #lastIndex += len(publisherID) + 1
                topicName = request[lastIndex:request.find(' ',lastIndex)]
                try:
                    self.topics[topicName]
                except KeyError:
                    print("Publisher tried to put data in non existent topic " + topicName)
                    self.publisher_socket.send("NON_EXISTENT".encode('utf-8'))
                    continue
                lastIndex += len(topicName) + 1
                messageText = request[lastIndex:]
                message = Message(messageText,self.topics[topicName])
                self.publisher_socket.send("ACK".encode('utf-8'))
                #self.topics[topicName].messages.append(message)

            if command == "ACK":
                req_list = request.split(" ") # 1 = sub_id 2 = topic 3 = message_ids
                #remove o subscriber da lista dee pesoas que ainda nao recebeu a mensagem
                topic = self.topics[req_list[2]]
                if topic == None:
                    print("Error in ACK: the topic refered does not exist")
                for id in req_list[3].split(","):
                    index = topic.messageIndex(int(id))
                    if index != None:
                        topic.messages[index].removeSubscriberToDeliver(req_list[1])
                self.subscribers_socket.send("STUFF".encode('utf-8'))
                print("Acknowledge received for ids " + req_list[3])





class Topic:
    name = "" #Name of the topic
    subscribers = [] #Subscribers of the topic
    messages = [] #Messages of the topic
    def __init__(self,name):
        self.name = name
        self.subscribers = []
        self.messages = []
        self.lastMessageNr = 0
    def subscribe(self,userID): #Subscribe user userID to topic
        self.subscribers.append(userID)
    def unsubscribe(self,userID):   #Unsubcribe user userID from topic
        try:
            self.subscribers.remove(userID)
            for msg in self.messages:
                msg.removeSubscriberToDeliver(userID)
        except ValueError:
            print("User " + userID + " tried to unsubscribe topic " + self.name + " but it wasn't subscribed before")
    def messageCheck(self, messageID):
        for msg in self.messages:
            if msg.messageID == messageID:
                return True
        return False
    def messageIndex(self, messageID):
        for i in range(0, len(self.messages)):
            if str(self.messages[i].messageID) == str(messageID):
                return i

class Message:
    text = "" #text of the message
    subscribersLeft = [] #subscribers who still haven't received the message
    messageID = "" #ID of the message to match aknoledgments from clients
    def __init__(self,message,topic):
        self.text = message
        self.topic = topic #topic of the message
        try: #try to append the message to the topic
            self.topic.messages.append(self)
        except KeyError: #If topic does not exist raise error
            print("Message created for non existing topic")
            return
        #Assining id to message
        self.topic.lastMessageNr+=1
        self.messageID = str(self.topic.lastMessageNr)
        self.subscribersLeft = self.topic.subscribers.copy()
    #Removes a subscriber with the name subscriberName, used when a message is delivered
    def removeSubscriberToDeliver(self,subscriberName):
        try:
            self.subscribersLeft.remove(subscriberName)
        except ValueError:
            print("Tried to remove subscriber form lefTSubscriber list of topic " + self.topic.name + " that does not exist")
            return False
        #No one else needs to receive the message so might as well just delete it
        if len(self.subscribersLeft) == 0:
            try:
                self.topic.messages.remove(self)
                return True
            except ValueError:
                print("Message attempted to be deleted on topic " + self.topic.name + " but its not part of it")
                return False

    