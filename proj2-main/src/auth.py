import calendar
import time
from random import randint

#falta fazer caso n haja nenhum user registado
def verify_user_exists_console(user):
    for line in open("users.txt","r").readlines(): 
        login_info = line.split() 
        if user == login_info[0].split("#")[0]: 
            print("Choose another username.")
            print(" ")
            register()
            return False
    return True

def register_console():
    print("------  REGISTER  ------")
    username = input("Please input your desired username: ")
    gmt = time.gmtime()
    ts = calendar.timegm(gmt)
    if verify_user_exists(username):
        password = input("Please input your desired password: ")
        file = open("users.txt","a")
        file.write(username+ "#"+ str(ts))
        file.write(" ")
        file.write(password)
        file.write("\n")
        file.close()
        if login():
            print("You are now logged in...")
        else:
            print("You aren't logged in!")

def register(username, password):
    if verify_user_exists(username):
        return False
    file = open("users.txt","a")
    gmt = time.gmtime()
    ts = calendar.timegm(gmt)
    file.write(username+ "#"+ str(ts))
    file.write(" ")
    file.write(str(password))
    file.write(" ")
    #Also needs to assign a port so that whenever someone tries to connect to this user, the port is always the same
    file.write(str(randint(2000,65000)))
    file.write("\n")
    file.close()
    return True

def verify_user_exists(user):
    try:
        for line in open("users.txt","r").readlines(): 
            login_info = line.split() 
            if user == login_info[0].split("#")[0]:
                return login_info[0]
        return ""
    except FileNotFoundError:
        return ""

#Returns a vector. If failed returns an empty array, if successful returns array with username with timestamp and port
def login(username,password):
    for line in open("users.txt","r").readlines(): 
        login_info = line.split() 
        if username == login_info[0].split("#")[0] and password == login_info[1]:
            #returns the port to create the socket
            return [login_info[0],login_info[2]]
    return []

def login_console():
    print(" ")
    print("------  LOGIN  ------")
    username = input("Please enter your username: ")
    password = input("Please enter your password: ")  
    for line in open("users.txt","r").readlines(): 
        login_info = line.split() 
        if username == login_info[0].split("#")[0] and password == login_info[1]:
            print("Auth Success!")
            return True
    print("Auth Fail.")
    return False

def remove(user):
    with open("users.txt", "r+") as f:
        lines = f.readlines()
        f.seek(0)
        for line in lines:
            splited = line.split()
            first = splited[0].split("#")[0]
            if first != user:
                f.write(line)
        f.truncate()



