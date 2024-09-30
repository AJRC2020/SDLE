import zmq
import datetime
import time
import threading

class Peer:
    port = "4000"
    ip = "127.0.0.1"
    peer_ip = "127.0.0.1"
    def __init__(self, name, password, peer_port,  ip=ip, port=port,peer_ip=peer_ip) -> None:
        print("Creating peer")
        self.ip = ip
        self.port = port
        self.name = name
        self.peer_port = peer_port #after it has to get it from server
        self.peer_ip = peer_ip
        self.subscribed = {}
        context = zmq.Context()
        self.server_socket = context.socket(zmq.REQ)
        self.server_socket.connect('tcp://' + ip + ':' + port)
        #if self.server_socket == None:
        #    print("Failed to connect peer to server")
        #    return None
        #login_msg = "login " + name + " " + password
        #self.server_socket.send(login_msg.encode("utf-8"))
        #self.name = self.server_socket.recv()
        #section to add login
        self.peer_socket = context.socket(zmq.REP)
        self.peer_socket.bind('tcp://' + peer_ip + ":" + str(peer_port))
        print("Started peer socket on " + 'tcp://' + peer_ip + ":" + str(peer_port))
        self.pathname = "messages/" + name + "_messages.txt"
        with open(self.pathname, 'a+') as file:
            file.close()

        #SUBSCRIBERS PART
        self.pathnamesubs = "followed/" + name + "_followed.txt"
        with open(self.pathnamesubs, 'a+') as filesubs:
            filesubs.close()
        with open(self.pathnamesubs, 'r+') as filesubs:
            #put in dictionary the followed people
            for line in filesubs.readlines():
                user = line.split(" ")[0]
                address = (line.split(" ")[1]).strip("\n")
                self.subscribed[user] = address
            filesubs.close()

    def create_message(self, message):
        file = open(self.pathname, 'r+')
        content = file.read()
        file.seek(0, 0)
        timestamp = datetime.datetime.now()
        final_message = self.name + "-" + message.replace("-", "$%") + "-" + timestamp.strftime("%Y/%m/%d %H:%M:%S")
        file.write(final_message + "\n" + content)
        file.close()
        

    def show(self):
        self.get_sub_messages()
        file = open(self.pathname, 'r')
        content = []
        message_list = []
        for line in file.readlines():
            line = line.strip("\n")
            (name, message, time) = line.split('-')
            time_interval = datetime.datetime.now() - datetime.datetime.strptime(time, '%Y/%m/%d %H:%M:%S')
            time_interval = int(round(time_interval.total_seconds()))
            unit = ""
            if time_interval == 1:
                unit = "second"
            elif time_interval < 60:
                unit = "seconds"
            elif time_interval >= 60 and time_interval < 120:
                time_interval = 1
                unit = "minute"
            elif time_interval < 3600:
                time_interval = int(round(time_interval / 60))
                unit = "minutes"
            elif time_interval >= 3600 and time_interval < 7200:
                time_interval = 1
                unit = "hour"
            elif time_interval < 86400:
                time_interval = int(round(time_interval / 3600))
                unit = "hours"
            elif time_interval < 172800:
                time_interval = 1
                unit = "day"
            else:
                file.close()
                self.update_messages(content)
                return None

            content.append(line + '\n')
            print(name + ": " + message.replace("$%", "-") + " - " + str(time_interval) + " " + unit + " ago")
            #message_list is the return array that has the information in the format to be printed in the interface
            #That is username (time ago)\nmessage
            message_list.append(name.split("#")[0] + " ("  + str(time_interval) + " " + unit + " ago)\n" + message.replace("$%", "-"))

        file.close()
        return message_list


    def subscribe(self, user, IPandPort):
        print("Subscribing to user " + user + " at " + IPandPort)
        #Check if user is not subscribing itself
        if self.name == user:
            print("WARNING: You can't follow your own self")
            return None
        #Check if user is not already subscribed
        elif user in self.subscribed.keys():
            print("WARNING: You already follow " + user)
        else:
            #Add user to subscribed users
            IPandPort.strip("\n")
            self.subscribed[user] = IPandPort  

            #Save newly subscirbed users to file with all subscriptions
            subs = open(self.pathnamesubs, 'r+')
            content = subs.read()
            subs.seek(0, 0)
            subs.write(user +" "+ IPandPort + "\n" + content)
            subs.close()

            #ending
            print("SUCCESS: You are following " + user + " now")
            return True
        return 
    


    def unsubscribe(self, user):
        file = open(self.pathname, 'r')
        content = []
        for line in file.readlines():
            line.strip("\n")
            (name, _, _) = line.split("-")
            if name != user:
                content.append(line)
        
        self.update_messages(content)
        print(self.subscribed)
        self.subscribed.pop(user)

    def update_messages(self, content):
        file = open(self.pathname, 'w')
        for line in content:
            file.write(line)

    #Get the messages from the subsribers
    def get_sub_messages(self):
        #for each subscription
        for user in self.subscribed.keys():
            print("Fetching messages from user " + user + " from " + str(self.subscribed[user]))
            #Creates a socket
            context = zmq.Context()
            request_socket = context.socket(zmq.REQ)
            request_socket.setsockopt(zmq.LINGER,0)
            request_socket.connect("tcp://" + self.ip + ":" + str(self.subscribed[user][self.subscribed[user].find(":")+1:]))
            #If failed to create socket
            if request_socket is None:
                request_socket.close()
                self.get_from_others(self.subscribed[user])
            else:
                #Attempting to get messages
                timestamp = datetime.datetime.now()
                request_socket.send_string("GET " + timestamp.strftime("%Y/%m/%d %H:%M:%S"))
                #setting timeout to 1 second
                request_socket.RCVTIMEO = 1000
                content = ""
                try:
                    content = request_socket.recv()
                except zmq.error.Again:
                    #if nothing is received
                    print("Failed to retrieve messages from user " + user)
                    request_socket.close()
                    continue
                content = content.decode('utf-8')
                print("GET RESPONSE:" + content)
                if content != "":
                    self.write_sub_to_file(content)
        
                
            
    def get_from_others(self, sub):
        #mandar request para todos os users que segues e ele vê as mensagens 
        #abrir ficheiro dos outros em doc, se encontrar da pessoa q eu quero dar show, se não, dá erro
        context = zmq.Context()
        request_socket = context.socket(zmq.REQ)
        with open(self.pathnamesubs, 'r+') as filesubs:
        #put in dictionary the followed people
            found = False
            for line in filesubs.readlines():
                user = line.split("\n")[0]
                with open("messages/" + user + "_messages.txt", 'r+') as filesubs2:
                    for line2 in filesubs2.readlines():
                        user2 = line2.split("\n")[0]
                        if user2 == sub:
                            #show das mensagens dele
                            found = True
                            break
                filesubs2.close() 
                if found == True:
                    break
        filesubs.close() 
        #request_socket.connect("tcp://" + self.ip + ":" + str(self.subscribed[user]))
        

        

    def write_sub_to_file(self, content):
        lines = content.split("\n")
        file = open(self.pathname, 'r+')
        content = file.readlines()
        for line in lines:
            foundLine = False
            inserted = False
            print("Inserting line: " + line)
            for line_read in content:
                print("Analysing line: " + line_read)
                (_, _, time_new) = line.split("-")
                (_, _, time_old) = line_read.split("-")
                if(line == line_read[:-1]):
                    print("Message already exists!")
                    foundLine=True
                    break
                if (datetime.datetime.strptime(time_new, '%Y/%m/%d %H:%M:%S') > datetime.datetime.strptime(time_old[:-1], '%Y/%m/%d %H:%M:%S')):
                    index = content.index(line_read)
                    content.insert(index, line + "\n")
                    print("Inserting now")
                    inserted = True
                    break
            if not foundLine and not inserted:
                print("Inserting in the end")
                content.append(line + '\n')
        file.close()
        self.update_messages(content)

    def send_my_messages(self, timestamp):
        print("DEBUG composing my messages. Given timestamp " + str(timestamp))
        content = ""
        file = open(self.pathname, 'r')
        for line in file.readlines():
            (name, _, stamp) = line.split("-")
            print("DEBUG timestamp of message is " + str(stamp[:-1]))
            #time1 - timestamp of the request time
            time1 = datetime.datetime.strptime(timestamp, '%Y/%m/%d %H:%M:%S')
            #time2 - timestamp of the message time
            time2 = datetime.datetime.strptime(stamp[:-1], '%Y/%m/%d %H:%M:%S')
            if name == self.name and time2 < time1:
                print("DEBUG adding line to content")
                content += line
        return content[:-1]

    def get_lastest_message(self, user):
        file = open(self.pathname, 'r')
        for line in file.readlines():
            (name, _, timestamp) = line.split("-")
            if name == user:
                return timestamp[:-1]

        return "2000/01/01 00:00:00"

    def run(self):
        while True:
            #try:
            request = self.peer_socket.recv()
            #except zmq.error.ZMQError:
            #    print("Unknown error while trying to receive request")
            #    continue
            if type(request) != str:
                request = request.decode('utf-8')
            print("REQUEST: " + request)
            if len(request) >= 3:
                if request[:3] == "GET":
                    print("Received get request")
                    if len(request) == 3:
                        print("Missing timestamp in GET request!")
                        self.peer_socket.send_string("ERROR")
                        continue
                    timestamp = request[request.find(" ")+1:]
                    return_content = self.send_my_messages(timestamp)
                    self.peer_socket.send_string(return_content)
                    print("GET request satisfied ("+ return_content + ")")
                else:
                    self.peer_socket.send_string("ERROR")
            else:
                self.peer_socket.send_string("ERROR")
