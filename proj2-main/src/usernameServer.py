import zmq
from time import time
from random import randint
import sys
from threading import Thread

# --------------- INSTRUCTIONS -----------------
#
#   To run: python usernameServer.py [-port port_nr]
#
#   Can be interacted in two ways:
#     - CONSOLE
#       Use add command to add an entry in the database, show to see the complete database or help for all the commands
#     - SOCKET CONNECTION
#       Connect to socket and send message in the format 'USERNAME:username#timestamp:ip:port' in wich username, timestamp, ip and port refer to the connecting user's data
#       The port of the server is by default 4000, if not available is random but displayed when run and can be set manually with -port tag






#Contains userAdressPairs like {"userAdressPair#1290380": "127.0.0.1:1900"}
userAdressPairs = {}
localIP = "127.0.0.1"
localPort = ""
version = -1
def loadUserAdressPairsFromFile(filename):
    global version
    try:
        f = open(filename,'r')
    except FileNotFoundError:
        return -1
    readLines = 0
    for line in f:
        if readLines == 0:
            version = int(line[8:])
        else:
            if line[-1] == '\n':
                line = line[:-1]
            i = line.find(':')
            userAdressPairs[line[:i]] = line[i+1:]
        readLines +=1
    f.close()
    return readLines

def saveUserAdressPairsToFile(filename):
    global version
    f = open(filename,'wt')
    f.write("version=" + str(version) + "\n")
    writtenLines = 1
    for userAdressPair in userAdressPairs:
        f.write(userAdressPair + ":" + userAdressPairs[userAdressPair] + "\n") #writting lines like "userAdressPair#1290380:127.0.0.1:1900"
        writtenLines += 1
    f.close()
    return writtenLines

#userAdressPair is like "bob#12312" and IPandPort is like "127.0.0.1:38299"
def addUserAdressPair(username,IPandPort):
    global version
    userText = username[:username.find("#")]
    for user in userAdressPairs:
        if user[:user.find("#")] == userText:
            return False
    if(username.find(':') != -1 or username.find('|') != -1):
        return False
    userAdressPairs[username] = IPandPort
    version +=1
    saveUserAdressPairsToFile("userAdressDatabase.txt")
    return True

def updateUserAddress(username, IPandPort):
    global version
    userAdressPairs[username] = IPandPort
    version +=1
    saveUserAdressPairsToFile("userAdressDatabase.txt")
    return True

#userAdressPair is like "bob#121324321"
def removeUserAdressPair(userAdressPair):
    for user in userAdressPairs:
        if user == userAdressPair:
            userAdressPairs.pop(user)
            return True
            version += 1
    return False

#returns if the user is in the database
def checkUserInDatabase(username, IPandPort):
    if username not in userAdressPairs:
        print("User performing the request is not in the database! Adding " + str(username) + ":" + IPandPort)
        success = addUserAdressPair(username,IPandPort)
    elif IPandPort != userAdressPairs[username]:
        print("User performing the request has a new IP and Port! Updating user " + str(username) + " to " + IPandPort)
        success = updateUserAddress(username,IPandPort)

socket = None

def main():
    global socket,localIP,localPort
    #Check if alternative IP or port were given in the arguments
    for i in range(len(sys.argv)):
        if sys.argv[i] == "-port":
            try:
                if int(sys.argv[i+1]) <= 1024 or int(sys.argv[i+1]) > 65535:
                    print("Invalid port given as argument, must be between 1025 and 65535")
                localPort = sys.argv[i+1]
            except:
                print("Invalid port given as argument, must be numeric!")
            i+=1
        if sys.argv[i] == "-ip":
            localIP = sys.argv[i]
            i+=1


    #Starting the server
    print("-------------- USERNAME SERVER --------------")
    print("Starting username server")
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    if localPort == "":
        try:
            socket.bind("tcp://" + localIP + ":4000")
            localPort = "4000"
        except zmq.error.ZMQError:
            localPort = str(socket.bind_to_random_port("tcp://" + localIP))
    else:
        socket.bind("tcp://" + localIP + ":" + localPort)
    print("Socket started on port " + localPort)
    loadUserAdressPairsFromFile("userAdressDatabase.txt")
    print("Loaded username data")
    print("Waiting for new requests...")
    print("---------------------------------------------")
    Thread(target=serverThread).start()
    Thread(target=consoleThread).start()

def serverThread():
    global socket
    while True:
        request = socket.recv().decode('utf-8')
        print("                           ", end="\r")
        #USERNAMES:username#2134123:127.0.0.1:9832
        if len(request) > 10:
            if request[:10] == "USERNAMES:":
                print("Received USERNAME request with user info: "+ request[10:])
                splitID = request.find(":",11)
                username = request[10:splitID]
                IPandPort = request[splitID+1:]
                #Add sending user to database
                checkUserInDatabase(username,IPandPort)
                #Send known users back
                reply = ""
                for user in userAdressPairs:
                    if len(user) == 0:
                        continue
                    reply += user + ":" + userAdressPairs[user] + "|"
                socket.send(reply.encode('utf-8'))
                print("Sent username list")
        elif request == "USERNAMES":
            print("Received USERNAME request without user info")
            #Send known users back
            reply = ""
            print(userAdressPairs)
            for user in userAdressPairs:
                if len(user) == 0:
                    continue
                reply += user + ":" + userAdressPairs[user] + "|"
            socket.send(reply.encode('utf-8'))
            print(reply)
            print("Sent username list")
        print("---------------------------------------------")

def consoleThread():
    while True:
        try:
            command = input()
        except:
            break
        if len(command) >= 3:
            if command[0:3] == "add":
                parts = command.split()
                if len(parts) != 3:
                    print("Invalid number of add arguments")
                    print("---------------------------------------------")
                    continue
                addUserAdressPair(parts[1] + "#" + str(int(time())),parts[2])
                print("---------------------------------------------")
                continue
        if command == "show" or command == "display":
            for username in userAdressPairs:
                print(username + " - " + userAdressPairs[username])
            print("---------------------------------------------")
            continue
        if command == "help":
            print("Available commands:")
            print(" - add [username] [ip:port] ")
            print("---------------------------------------------")
            continue
        if command == "quit" or command =="q":
            print("Shutting down server")
            exit()
        print("Unknown command. Type 'help' for a list of available commands")
        print("---------------------------------------------")
                


if __name__ == "__main__":
    main()
