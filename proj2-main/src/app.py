from peer import Peer
import sys
#For GUI stuff
from tkinter import *
from PIL import ImageTk,Image
from auth import *
from threading import Thread
import zmq

APP_NAME = "PeerMessage"
TEXT_ORANGE_COLOR = '#ffb500'
TEXT_WHITE_COLOR = "#e5e5e5"
BACKGROUND_COLOR = "#28272b"
BUTTON_BACKGROUND_COLOR = "#212123"
BUTTON_CLICKED_BACKGROUND_COLOR = "#1c1c1e"
BUTTON_CLICKED_TEXT_COLOR = '#dd9e00'

usernameServerIP = "127.0.0.1"
usernameServerPort = "4000"

userPeerObject = None

authenticated = False

currentServerUsernames = {}

#Starting window
window = Tk(baseName=None,  className='Tk',  useTk=1)
window.geometry('500x1000')
window.configure(bg = '#28272b')
window.title(APP_NAME)
#window.iconbitmap('resources/app_icon.ico')
#Initializing interface variables
login_user_var = StringVar()
login_password_var = StringVar()
register_user_var = StringVar()
register_password_var = StringVar()
specify_address_username_var = StringVar()
specify_address_ip_var = StringVar()
specify_address_port_var = StringVar()
username_server_ip_var = StringVar()
username_server_port_var = StringVar()
peer_ip_var = StringVar()
#Loading images
logo_img = ImageTk.PhotoImage(Image.open("resources/app_icon_300x300.png"))
new_message_img = ImageTk.PhotoImage(Image.open("resources/new_message.png").resize((50,50)))
user_icon_img = ImageTk.PhotoImage(Image.open("resources/user_icon.png").resize((70,70)))
network_icon_img = ImageTk.PhotoImage(Image.open("resources/network.png").resize((50,50)))
add_user_img = ImageTk.PhotoImage(Image.open("resources/add_user.png").resize((50,50)))
reload_icon_img = ImageTk.PhotoImage(Image.open("resources/reload_icon.png").resize((50,50)))
back_icon_img = ImageTk.PhotoImage(Image.open("resources/back_icon.png").resize((50,50)))
settings_img = ImageTk.PhotoImage(Image.open("resources/settings.png").resize((50,50)))

#Changing active screens
activeScreen = "start"

#Entry list
entryList = []
def clearEntries():
    for entry in entryList:
        entry.delete(0,END)


def attemptLogin():
    global loginScreenWarningText,authenticated, userPeerObject
    name = login_user_var.get()
    password = login_password_var.get()
    if len(name) == 0:
        loginScreenWarningText="Please enter a user"
        setActiveScreenLogin()
        return False
    if len(password) == 0:
        loginScreenWarningText="Please enter a password"
        setActiveScreenLogin()
        return False
    success = login(name,password)
    if len(success) == 0:
        loginScreenWarningText = "Incorrect Credentials"
        setActiveScreenLogin()
    else:
        try:
            userPeerObject = Peer(success[0],password,int(success[1]))
            Thread(target=userPeerObject.run).start()
            setActiveScreenMain()
            authenticated = True
            return True
        except zmq.error.ZMQBaseError:
            loginScreenWarningText = "ERROR\nAnother process is\nusing the user port"
            setActiveScreenLogin()
            return False

def attemptRegister():
    global registerScreenWarningText,authenticated, startScreenWarningText
    name = register_user_var.get()
    password = register_password_var.get()
    if len(name) == 0:
        registerScreenWarningText="Please enter a user"
        setActiveScreenRegister()
        return False
    if len(password) == 0:
        registerScreenWarningText="Please enter a password"
        setActiveScreenRegister()
        return False
    if name.find('#') != -1 or name.find(' ') != -1:
        registerScreenWarningText="Username contains invalid characters"
        setActiveScreenRegister()
        return False
    success = register(name,password)
    if not success:
        registerScreenWarningText = "User already exists"
        setActiveScreenRegister()
        return False
    else:
        startScreenWarningText = "Account successfully created"
        setActiveScreenStart()
        return True

new_message_textbox = None
def attemptNewMessage():
    global new_message_textbox,mainScreenWarningText
    messageText = new_message_textbox.get("1.0","end-1c")
    userPeerObject.create_message(messageText)
    mainScreenWarningText = "Message Posted"
    setActiveScreenMain()
    return True

def attemptSubscription():
    global userPeerObject,specifyAddressScreenWarningText, networkScreenWarningText
    username = specify_address_username_var.get()
    ip = specify_address_ip_var.get()
    port = specify_address_port_var.get()
    if len(username) == 0:
        specifyAddressScreenWarningText="Please enter a username"
        setActiveScreenSpecifyAddress()
        return False
    if str(username).find("#") == -1:
        specifyAddressScreenWarningText="Please enter the complete username!\nIt can be found on the other user's\nuser info (click on the user icon)"
        setActiveScreenSpecifyAddress()
        return False
    if len(ip) == 0:
        specifyAddressScreenWarningText="Please enter an ip"
        setActiveScreenSpecifyAddress()
        return False
    if len(port) == 0:
        specifyAddressScreenWarningText="Please enter a port"
        setActiveScreenSpecifyAddress()
        return False
    userPeerObject.subscribe(str(username),str(ip) + ":" + str(port))
    networkScreenWarningText = "Subscribed user " + str(username)
    setActiveScreenNetwork()
    clearEntries()
    return True

def attemptUserServerSubscription():
    global serverUsernameList, networkScreenWarningText
    selectedIndex = serverUsernameList.curselection()
    if len(selectedIndex) == 1:
        selectedIndex = selectedIndex[0]
        user = list(currentServerUsernames.keys())[selectedIndex]
        IPandPort = currentServerUsernames[user]
        userPeerObject.subscribe(user,IPandPort)
        print("Subscribed to user " + user)
        networkScreenWarningText = "Subscribed user " + user[:user.find("#")]
        setActiveScreenNetwork()
        return True
    return False

def attemptUserUnsubscription():
    global subscriptions_list, networkScreenWarningText
    selectedIndex = subscriptions_list.curselection()
    #This means something is selected
    if len(selectedIndex) == 1:
        selectedIndex = selectedIndex[0]
        user = list(userPeerObject.subscribed.keys())[selectedIndex]
        print("UNSUBSCRIBING USER: " + user)
        userPeerObject.unsubscribe(user)
        networkScreenWarningText = "Unsubscribed user " + user[:user.find("#")]
        setActiveScreenNetwork()
        return True
    return False

def getUsernamesFromServer():
    Thread(target=getUsernamesFromServerThread).start()

def getUsernamesFromServerThread():
    print("Attempting to retrieve usernames from server")
    global subscribeUserScreenWarningText,currentServerUsernames,usernameServerIP,usernameServerPort
    req_socket = zmq.Context().socket(zmq.REQ)
    req_socket.RCVTIMEO = 3000
    req_socket.connect("tcp://" + usernameServerIP + ":" + usernameServerPort)
    req_socket.send(("USERNAMES:" + str(userPeerObject.name) + ":" + str(userPeerObject.peer_ip) +":"+ str(userPeerObject.peer_port)).encode('utf-8'))
    result = ""
    try:
        result = req_socket.recv()
    except zmq.error.Again:
        subscribeUserScreenWarningText = "Failed to retrieve users"
        setActiveScreenSubscribeUser()
        return False
    users = result.decode('utf-8').split("|")
    currentServerUsernames = {}
    for user in users:
        username = user[:user.find(':')]
        IPandPort = user[user.find(":")+1:]
        if username == userPeerObject.name:
            continue
        currentServerUsernames[username] = IPandPort
    subscribeUserScreenWarningText = ""
    print("Retrieved new users")
    setActiveScreenSubscribeUser()
    return True

def attemptMessagesRefresh():
    setActiveScreenMain()
    Thread(target=messageRefreshThread).start()

def messageRefreshThread():
    global mainScreenWarningText, userMessages
    newMessages = userPeerObject.show()
    if newMessages is not None:
        aux = []
        for message in newMessages:
            message_parts = message.split('\n')
            aux.append(message_parts[0])
            aux.append(message_parts[1])
            aux.append("")
    userMessages = aux
    mainScreenWarningText = "updated messages"
    setActiveScreenMain()

def setUsernameServerIPandPort():
    global usernameServerIP,usernameServerPort,username_server_ip_var,username_server_port_var,subscribeUserScreenWarningText
    usernameServerIP = str(username_server_ip_var.get())
    usernameServerPort = str(username_server_port_var.get())
    userPeerObject.ip = usernameServerIP
    userPeerObject.port = usernameServerPort
    print("Changed server ip and port to " + usernameServerIP + ":" + usernameServerPort)
    subscribeUserScreenWarningText = "Server IP and Port changed"
    setActiveScreenSubscribeUser()
    return True

def setPeerPort():
    global mainScreenWarningText
    new_ip = peer_ip_var.get()
    userPeerObject.peer_ip = new_ip
    mainScreenWarningText = "IP address updated"
    setActiveScreenMain()


#t1 = threading.Thread(target=userPeerObject.run)
#t1.start()


startScreenWarningText = ""
def setActiveScreenStart():
    global window,activeScreen
    print("Switching to start page")

    for widget in window.winfo_children():
        widget.destroy()
    activeScreen = "login"

    startPage = Frame(window,width=500,height=1000,bg=BACKGROUND_COLOR)
    startPage.pack()

    start_logo=Label(startPage,image=logo_img, border=0)
    start_logo.place(x=100,y=100)

    login_button = Button(startPage,text="Log in",command=setActiveScreenLogin,fg=TEXT_ORANGE_COLOR,bg=BUTTON_BACKGROUND_COLOR,font="Courier",activebackground=BUTTON_CLICKED_BACKGROUND_COLOR, activeforeground=BUTTON_CLICKED_TEXT_COLOR,relief=RIDGE,bd=0)
    login_button.place(x=150,y=500,width=200,height=50)

    register_button = Button(startPage,text="Register",command=setActiveScreenRegister,fg=TEXT_ORANGE_COLOR,bg=BUTTON_BACKGROUND_COLOR,font="Courier",activebackground=BUTTON_CLICKED_BACKGROUND_COLOR, activeforeground=BUTTON_CLICKED_TEXT_COLOR,relief=RIDGE,bd=0)
    register_button.place(x=150,y=600,width=200,height=50)
    
    warning_label = Label(text=startScreenWarningText,fg=TEXT_ORANGE_COLOR,font="courier",bg=BACKGROUND_COLOR)
    warning_label.place(x=250,y=750,anchor=CENTER)

loginScreenWarningText = ""
def setActiveScreenLogin():
    global window,activeScreen,loginScreenWarningText
    print("Switching to login page")
    for widget in window.winfo_children():
        widget.destroy()
    activeScreen = "login"

    loginPage = Frame(window,width=500,height=1000,bg=BACKGROUND_COLOR)
    loginPage.pack()

    title_label = Label(text="Log in",fg=TEXT_ORANGE_COLOR,font=("courier",30),bg=BACKGROUND_COLOR)
    title_label.place(x=170,y=150)

    username_label = Label(text="User:",fg=TEXT_ORANGE_COLOR,font="courier",bg=BACKGROUND_COLOR)
    username_label.place(x=130,y=260)
    username_inputbox = Entry(bg=BUTTON_BACKGROUND_COLOR,fg=TEXT_WHITE_COLOR, border = 0,font=("courier",14),textvariable= login_user_var)
    username_inputbox.place(x=200,y=250,width=200,height=50)
    username_inputbox.delete(0,END)
    
    password_label = Label(text="Password:",fg=TEXT_ORANGE_COLOR,font="courier",bg=BACKGROUND_COLOR)
    password_label.place(x=80,y=360)
    password_inputbox = Entry(bg=BUTTON_BACKGROUND_COLOR,fg=TEXT_WHITE_COLOR, border = 0,font=("courier",14),show="*",textvariable= login_password_var)
    password_inputbox.place(x=200,y=350,width=200,height=50)
    password_inputbox.delete(0,END)

    register_button = Button(loginPage,text="Log in",command=attemptLogin,fg=TEXT_ORANGE_COLOR,bg=BUTTON_BACKGROUND_COLOR,font="Courier",activebackground=BUTTON_CLICKED_BACKGROUND_COLOR, activeforeground=BUTTON_CLICKED_TEXT_COLOR,relief=RIDGE,bd=0)
    register_button.place(x=150,y=450,width=200,height=50)

    back_button = Button(loginPage,text="Back",command=setActiveScreenStart,fg=TEXT_ORANGE_COLOR,bg=BUTTON_BACKGROUND_COLOR,font="Courier",activebackground=BUTTON_CLICKED_BACKGROUND_COLOR, activeforeground=BUTTON_CLICKED_TEXT_COLOR,relief=RIDGE,bd=0)
    back_button.place(x=150,y=525,width=200,height=50)

    warning_label = Label(text=loginScreenWarningText,fg=TEXT_ORANGE_COLOR,font="courier",bg=BACKGROUND_COLOR)
    warning_label.place(x=250,y=700,anchor=CENTER)

registerScreenWarningText = ""
def setActiveScreenRegister():
    global window,activeScreen
    print("Switching to register page")
    for widget in window.winfo_children():
        widget.destroy()
    activeScreen = "login"

    loginPage = Frame(window,width=500,height=1000,bg=BACKGROUND_COLOR)
    loginPage.pack()

    title_label = Label(text="Register",fg=TEXT_ORANGE_COLOR,font=("courier",30),bg=BACKGROUND_COLOR)
    title_label.place(x=150,y=250)

    username_label = Label(text="User:",fg=TEXT_ORANGE_COLOR,font="courier",bg=BACKGROUND_COLOR)
    username_label.place(x=130,y=360)
    username_inputbox = Entry(bg=BUTTON_BACKGROUND_COLOR,fg=TEXT_WHITE_COLOR, border = 0,font=("courier",14),textvariable=register_user_var)
    username_inputbox.place(x=200,y=350,width=200,height=50)
    username_inputbox.delete(0,END)
    
    password_label = Label(text="Password:",fg=TEXT_ORANGE_COLOR,font="courier",bg=BACKGROUND_COLOR)
    password_label.place(x=80,y=460)
    password_inputbox = Entry(bg=BUTTON_BACKGROUND_COLOR,fg=TEXT_WHITE_COLOR, border = 0,font=("courier",14),show="*",textvariable=register_password_var)
    password_inputbox.place(x=200,y=450,width=200,height=50)
    password_inputbox.delete(0,END)

    register_button = Button(loginPage,text="Register",command=attemptRegister,fg=TEXT_ORANGE_COLOR,bg=BUTTON_BACKGROUND_COLOR,font="Courier",activebackground=BUTTON_CLICKED_BACKGROUND_COLOR, activeforeground=BUTTON_CLICKED_TEXT_COLOR,relief=RIDGE,bd=0)
    register_button.place(x=150,y=550,width=200,height=50)

    back_button = Button(loginPage,text="Back",command=setActiveScreenStart,fg=TEXT_ORANGE_COLOR,bg=BUTTON_BACKGROUND_COLOR,font="Courier",activebackground=BUTTON_CLICKED_BACKGROUND_COLOR, activeforeground=BUTTON_CLICKED_TEXT_COLOR,relief=RIDGE,bd=0)
    back_button.place(x=150,y=625,width=200,height=50)

    warning_label = Label(text=registerScreenWarningText,fg=TEXT_ORANGE_COLOR,font="courier",bg=BACKGROUND_COLOR)
    warning_label.place(x=250,y=730,anchor=CENTER)

userMessages = []
mainScreenWarningText=""
def setActiveScreenMain():
    global window,activeScreen,mainScreenWarningText,userMessages
    print("Switching to main page")
    for widget in window.winfo_children():
        widget.destroy()
    activeScreen = "main"

    mainPage = Frame(window,width=500,height=1000,bg=BACKGROUND_COLOR)
    mainPage.pack()

    mainScreenMessageListBox = Listbox(mainPage,bg=BUTTON_BACKGROUND_COLOR,bd=5,font="courier",selectbackground=BACKGROUND_COLOR,relief=FLAT,fg=TEXT_WHITE_COLOR,activestyle='none')
    mainScreenMessageListBox.delete(0,END)
    for i,message in enumerate(userMessages):
        mainScreenMessageListBox.insert(i,message)
    mainScreenMessageListBox.place(x=50,y=150,width=400,height=600)

    new_message_button = Button(mainPage,image=new_message_img,command=setActiveScreenNewMessage,fg=TEXT_ORANGE_COLOR,bg=BUTTON_BACKGROUND_COLOR,font="Courier",activebackground=BUTTON_CLICKED_BACKGROUND_COLOR, activeforeground=BUTTON_CLICKED_TEXT_COLOR,relief=RIDGE,bd=0)
    new_message_button.place(x=400,y=50,width=50,height=50)

    network_button = Button(mainPage,image=network_icon_img,command=setActiveScreenNetwork,fg=TEXT_ORANGE_COLOR,bg=BUTTON_BACKGROUND_COLOR,font="Courier",activebackground=BUTTON_CLICKED_BACKGROUND_COLOR, activeforeground=BUTTON_CLICKED_TEXT_COLOR,relief=RIDGE,bd=0)
    network_button.place(x=340,y=50,width=50,height=50)

    update_button = Button(mainPage,image=reload_icon_img,command=attemptMessagesRefresh,fg=TEXT_ORANGE_COLOR,bg=BUTTON_BACKGROUND_COLOR,font="Courier",activebackground=BUTTON_CLICKED_BACKGROUND_COLOR, activeforeground=BUTTON_CLICKED_TEXT_COLOR,relief=RIDGE,bd=0)
    update_button.place(x=280,y=50,width=50,height=50)

    user_icon = Button(mainPage,image=user_icon_img,command=setActiveScreenUserInfo,fg=TEXT_ORANGE_COLOR,bg=BUTTON_BACKGROUND_COLOR,font="Courier",activebackground=BUTTON_CLICKED_BACKGROUND_COLOR, activeforeground=BUTTON_CLICKED_TEXT_COLOR,relief=RIDGE,bd=0)
    user_icon.place(x=50,y=40,width=70,height=70)

    user_name = Label(text=userPeerObject.name.split("#")[0],fg=TEXT_ORANGE_COLOR,font=("courier",21),bg=BACKGROUND_COLOR)
    user_name.place(x=130,y=56)
    
    warning_label = Label(text=mainScreenWarningText,fg=TEXT_ORANGE_COLOR,font="courier",bg=BACKGROUND_COLOR)
    warning_label.place(x=250,y=125,anchor=CENTER)

def setActiveScreenNewMessage():
    global window,activeScreen,new_message_textbox
    print("Switching to new message page")
    for widget in window.winfo_children():
        widget.destroy()
    activeScreen = "new_message"

    mainPage = Frame(window,width=500,height=1000,bg=BACKGROUND_COLOR)
    mainPage.pack()

    title_label = Label(text="New Message",fg=TEXT_ORANGE_COLOR,font=("courier",30),bg=BACKGROUND_COLOR)
    title_label.place(x=250,y=100,anchor=CENTER)
    
    message_inputbox = Text(bg=BUTTON_BACKGROUND_COLOR,fg=TEXT_WHITE_COLOR, border = 0,font=("courier",14),bd=20,relief=FLAT)
    message_inputbox.place(x=50,y=150,width=400,height=300)
    new_message_textbox = message_inputbox
    

    confirm_button = Button(mainPage,text="Confirm",command=attemptNewMessage,fg=TEXT_ORANGE_COLOR,bg=BUTTON_BACKGROUND_COLOR,font="Courier",activebackground=BUTTON_CLICKED_BACKGROUND_COLOR, activeforeground=BUTTON_CLICKED_TEXT_COLOR,relief=RIDGE,bd=0)
    confirm_button.place(x=150,y=500,width=200,height=75)
    confirm_button = Button(mainPage,text="Back",command=setActiveScreenMain,fg=TEXT_ORANGE_COLOR,bg=BUTTON_BACKGROUND_COLOR,font="Courier",activebackground=BUTTON_CLICKED_BACKGROUND_COLOR, activeforeground=BUTTON_CLICKED_TEXT_COLOR,relief=RIDGE,bd=0)
    confirm_button.place(x=150,y=600,width=200,height=75)

subscriptions_list = None
networkScreenWarningText=""
def setActiveScreenNetwork():
    global window,activeScreen,networkScreenWarningText,subscriptions_list
    print("Switching to network page")
    for widget in window.winfo_children():
        widget.destroy()
    activeScreen = "main"

    mainPage = Frame(window,width=500,height=1000,bg=BACKGROUND_COLOR)
    mainPage.pack()

    subscribe_user_button = Button(mainPage,image=add_user_img,command=setActiveScreenSubscribeUser,fg=TEXT_ORANGE_COLOR,bg=BUTTON_BACKGROUND_COLOR,font="Courier",activebackground=BUTTON_CLICKED_BACKGROUND_COLOR, activeforeground=BUTTON_CLICKED_TEXT_COLOR,relief=RIDGE,bd=0)
    subscribe_user_button.place(x=400,y=50,width=50,height=50)

    back_button = Button(mainPage,image=back_icon_img,command=setActiveScreenMain,fg=TEXT_ORANGE_COLOR,bg=BUTTON_BACKGROUND_COLOR,font="Courier",activebackground=BUTTON_CLICKED_BACKGROUND_COLOR, activeforeground=BUTTON_CLICKED_TEXT_COLOR,relief=RIDGE,bd=0)
    back_button.place(x=50,y=50,width=50,height=50)

    title_label = Label(text="Your network",fg=TEXT_ORANGE_COLOR,font=("courier",24),bg=BACKGROUND_COLOR)
    title_label.place(x=250,y=75,anchor=CENTER)

    warning_label = Label(text=networkScreenWarningText,fg=TEXT_ORANGE_COLOR,font="courier",bg=BACKGROUND_COLOR)
    warning_label.place(x=250,y=125,anchor=CENTER)

    subscriptions_list = Listbox(mainPage,bg=BUTTON_BACKGROUND_COLOR,bd=5,font="courier",selectbackground=BACKGROUND_COLOR,relief=FLAT,fg=TEXT_WHITE_COLOR,activestyle='none')
    subscriptions_list.place(x=50,y=150,width=400,height=500)
    for i,subscription in enumerate(userPeerObject.subscribed.keys()):
        found = False
        for j,subscription2 in enumerate(userPeerObject.subscribed.keys()):
            if j==i:
                continue
            if subscription[:subscription.find("#")] == subscription2[:subscription2.find("#")]:
                found = True
                break
        if not found:
            subscription = subscription[:subscription.find("#")]
        subscriptions_list.insert(i,subscription)

    unsubscribe_button = Button(mainPage,text="Unsubscribe",command=attemptUserUnsubscription,fg=TEXT_ORANGE_COLOR,bg=BUTTON_BACKGROUND_COLOR,font="Courier",activebackground=BUTTON_CLICKED_BACKGROUND_COLOR, activeforeground=BUTTON_CLICKED_TEXT_COLOR,relief=RIDGE,bd=0)
    unsubscribe_button.place(x=250,y=700,width=150,height=50,anchor=CENTER)

serverUsernameList = None
subscribeUserScreenWarningText=""
def setActiveScreenSubscribeUser():
    global window,activeScreen,subscribeUserScreenWarningText,serverUsernameList,currentServerUsernames
    print("Switching to subscribe user page")
    for widget in window.winfo_children():
        widget.destroy()
    activeScreen = "main"

    mainPage = Frame(window,width=500,height=1000,bg=BACKGROUND_COLOR)
    mainPage.pack()

    update_button = Button(mainPage,image=reload_icon_img,command=getUsernamesFromServer,fg=TEXT_ORANGE_COLOR,bg=BUTTON_BACKGROUND_COLOR,font="Courier",activebackground=BUTTON_CLICKED_BACKGROUND_COLOR, activeforeground=BUTTON_CLICKED_TEXT_COLOR,relief=RIDGE,bd=0)
    update_button.place(x=340,y=50,width=50,height=50)

    specify_address_button = Button(mainPage,text="Specify address",command=setActiveScreenSpecifyAddress,fg=TEXT_ORANGE_COLOR,bg=BUTTON_BACKGROUND_COLOR,font="Courier",activebackground=BUTTON_CLICKED_BACKGROUND_COLOR, activeforeground=BUTTON_CLICKED_TEXT_COLOR,relief=RIDGE,bd=0)
    specify_address_button.place(x=110,y=50,width=220,height=50)
    
    back_button = Button(mainPage,image=back_icon_img,command=setActiveScreenNetwork,fg=TEXT_ORANGE_COLOR,bg=BUTTON_BACKGROUND_COLOR,font="Courier",activebackground=BUTTON_CLICKED_BACKGROUND_COLOR, activeforeground=BUTTON_CLICKED_TEXT_COLOR,relief=RIDGE,bd=0)
    back_button.place(x=50,y=50,width=50,height=50)

    settings_button = Button(mainPage,image=settings_img,command=setActiveScreenSettings,fg=TEXT_ORANGE_COLOR,bg=BUTTON_BACKGROUND_COLOR,font="Courier",activebackground=BUTTON_CLICKED_BACKGROUND_COLOR, activeforeground=BUTTON_CLICKED_TEXT_COLOR,relief=RIDGE,bd=0)
    settings_button.place(x=400,y=50,width=50,height=50)

    serverUsernameList = Listbox(mainPage,bg=BUTTON_BACKGROUND_COLOR,bd=5,font="courier",selectbackground=BACKGROUND_COLOR,relief=FLAT,fg=TEXT_WHITE_COLOR,activestyle='none')
    serverUsernameList.place(x=50,y=150,width=400,height=500)
    for i,user in enumerate(currentServerUsernames):
        username = user[:user.find("#")]
        for j,user2 in enumerate(currentServerUsernames):
            if i == j:
                continue
            if username == user2[:user2.find("#")]:
                username += user[user.find("#"):]
                break
        serverUsernameList.insert(i,username)

    subscribe_button = Button(mainPage,text="Subscribe",command=attemptUserServerSubscription,fg=TEXT_ORANGE_COLOR,bg=BUTTON_BACKGROUND_COLOR,font="Courier",activebackground=BUTTON_CLICKED_BACKGROUND_COLOR, activeforeground=BUTTON_CLICKED_TEXT_COLOR,relief=RIDGE,bd=0)
    subscribe_button.place(x=250,y=700,width=130,height=50,anchor=CENTER)

    warning_label = Label(text=subscribeUserScreenWarningText,fg=TEXT_ORANGE_COLOR,font="courier",bg=BACKGROUND_COLOR)
    warning_label.place(x=250,y=125,anchor=CENTER)

specifyAddressScreenWarningText=""
def setActiveScreenSpecifyAddress():
    global window,activeScreen,specifyAddressScreenWarningText,entryList
    print("Switching to specify address page")
    for widget in window.winfo_children():
        widget.destroy()
    activeScreen = "main"

    specifyUserPage = Frame(window,width=500,height=1000,bg=BACKGROUND_COLOR)
    specifyUserPage.pack()

    title_label = Label(text="Specify Address",fg=TEXT_ORANGE_COLOR,font=("courier",30),bg=BACKGROUND_COLOR)
    title_label.place(x=250,y=250,anchor=CENTER)

    username_label = Label(text="Username:",fg=TEXT_ORANGE_COLOR,font="courier",bg=BACKGROUND_COLOR)
    username_label.place(x=80,y=360)
    username_inputbox = Entry(bg=BUTTON_BACKGROUND_COLOR,fg=TEXT_WHITE_COLOR, border = 0,font=("courier",14),textvariable=specify_address_username_var)
    username_inputbox.place(x=200,y=350,width=200,height=50)
    entryList.append(username_inputbox)
    
    ip_label = Label(text="IP:",fg=TEXT_ORANGE_COLOR,font="courier",bg=BACKGROUND_COLOR)
    ip_label.place(x=150,y=460)
    ip_inputbox = Entry(bg=BUTTON_BACKGROUND_COLOR,fg=TEXT_WHITE_COLOR, border = 0,font=("courier",14),textvariable=specify_address_ip_var)
    ip_inputbox.place(x=200,y=450,width=200,height=50)
    entryList.append(ip_inputbox)

    port_label = Label(text="Port:",fg=TEXT_ORANGE_COLOR,font="courier",bg=BACKGROUND_COLOR)
    port_label.place(x=130,y=560)
    port_inputbox = Entry(bg=BUTTON_BACKGROUND_COLOR,fg=TEXT_WHITE_COLOR, border = 0,font=("courier",14),textvariable=specify_address_port_var)
    port_inputbox.place(x=200,y=550,width=200,height=50)
    entryList.append(port_inputbox)

    register_button = Button(specifyUserPage,text="Subscribe",command=attemptSubscription,fg=TEXT_ORANGE_COLOR,bg=BUTTON_BACKGROUND_COLOR,font="Courier",activebackground=BUTTON_CLICKED_BACKGROUND_COLOR, activeforeground=BUTTON_CLICKED_TEXT_COLOR,relief=RIDGE,bd=0)
    register_button.place(x=150,y=650,width=200,height=50)

    back_button = Button(specifyUserPage,text="Back",command=setActiveScreenSubscribeUser,fg=TEXT_ORANGE_COLOR,bg=BUTTON_BACKGROUND_COLOR,font="Courier",activebackground=BUTTON_CLICKED_BACKGROUND_COLOR, activeforeground=BUTTON_CLICKED_TEXT_COLOR,relief=RIDGE,bd=0)
    back_button.place(x=150,y=725,width=200,height=50)


    warning_label = Label(text=specifyAddressScreenWarningText,fg=TEXT_ORANGE_COLOR,font="courier",bg=BACKGROUND_COLOR)
    warning_label.place(x=250,y=125,anchor=CENTER)

def setActiveScreenSettings():
    global window,activeScreen,specifyAddressScreenWarningText,entryList,usernameServerIP,usernameServerPort
    print("Switching to settings page")
    for widget in window.winfo_children():
        widget.destroy()
    activeScreen = "settings"

    specifyUserPage = Frame(window,width=500,height=1000,bg=BACKGROUND_COLOR)
    specifyUserPage.pack()

    title_label = Label(text="Username server\nsettings",fg=TEXT_ORANGE_COLOR,font=("courier",30),bg=BACKGROUND_COLOR)
    title_label.place(x=250,y=250,anchor=CENTER)
    
    ip_label = Label(text="IP:",fg=TEXT_ORANGE_COLOR,font="courier",bg=BACKGROUND_COLOR)
    ip_label.place(x=150,y=360)
    ip_inputbox = Entry(bg=BUTTON_BACKGROUND_COLOR,fg=TEXT_WHITE_COLOR, border = 0,font=("courier",14),textvariable=username_server_ip_var)
    ip_inputbox.place(x=200,y=350,width=200,height=50)
    ip_inputbox.delete(0,END)
    ip_inputbox.insert(0,usernameServerIP)
    entryList.append(ip_inputbox)

    port_label = Label(text="Port:",fg=TEXT_ORANGE_COLOR,font="courier",bg=BACKGROUND_COLOR)
    port_label.place(x=130,y=460)
    port_inputbox = Entry(bg=BUTTON_BACKGROUND_COLOR,fg=TEXT_WHITE_COLOR, border = 0,font=("courier",14),textvariable=username_server_port_var)
    port_inputbox.place(x=200,y=450,width=200,height=50)
    port_inputbox.delete(0,END)
    port_inputbox.insert(0,usernameServerPort)
    entryList.append(port_inputbox)

    set_button = Button(specifyUserPage,text="Set",command=setUsernameServerIPandPort,fg=TEXT_ORANGE_COLOR,bg=BUTTON_BACKGROUND_COLOR,font="Courier",activebackground=BUTTON_CLICKED_BACKGROUND_COLOR, activeforeground=BUTTON_CLICKED_TEXT_COLOR,relief=RIDGE,bd=0)
    set_button.place(x=150,y=600,width=200,height=50)

    back_button = Button(specifyUserPage,text="Back",command=setActiveScreenSubscribeUser,fg=TEXT_ORANGE_COLOR,bg=BUTTON_BACKGROUND_COLOR,font="Courier",activebackground=BUTTON_CLICKED_BACKGROUND_COLOR, activeforeground=BUTTON_CLICKED_TEXT_COLOR,relief=RIDGE,bd=0)
    back_button.place(x=150,y=700,width=200,height=50)


    warning_label = Label(text=specifyAddressScreenWarningText,fg=TEXT_ORANGE_COLOR,font="courier",bg=BACKGROUND_COLOR)
    warning_label.place(x=250,y=125,anchor=CENTER)


def setActiveScreenUserInfo():
    global window,activeScreen
    print("Switching to user info page")
    for widget in window.winfo_children():
        widget.destroy()
    activeScreen = "userInfo"

    userInfoPage = Frame(window,width=500,height=1000,bg=BACKGROUND_COLOR)
    userInfoPage.pack()

    title_label = Label(text=userPeerObject.name[:userPeerObject.name.find("#")],fg=TEXT_ORANGE_COLOR,font=("courier",30),bg=BACKGROUND_COLOR)
    title_label.place(x=250,y=250,anchor=CENTER)
    
    complete_user_label = Label(text=("Complete user: " + userPeerObject.name),fg=TEXT_ORANGE_COLOR,font="courier",bg=BACKGROUND_COLOR)
    complete_user_label.place(x=250,y=360,anchor=CENTER)

    ip_label = Label(text="IP:",fg=TEXT_ORANGE_COLOR,font="courier",bg=BACKGROUND_COLOR)
    ip_label.place(x=150,y=460)
    ip_inputbox = Entry(bg=BUTTON_BACKGROUND_COLOR,fg=TEXT_WHITE_COLOR, border = 0,font=("courier",14),textvariable=peer_ip_var)
    ip_inputbox.place(x=200,y=450,width=200,height=50)
    ip_inputbox.delete(0,END)
    ip_inputbox.insert(0,userPeerObject.ip)

    port_label = Label(text="Port: " + str(userPeerObject.peer_port),fg=TEXT_ORANGE_COLOR,font="courier",bg=BACKGROUND_COLOR)
    port_label.place(x=250,y=390,anchor=CENTER)

    set_button = Button(userInfoPage,text="Set",command=setPeerPort,fg=TEXT_ORANGE_COLOR,bg=BUTTON_BACKGROUND_COLOR,font="Courier",activebackground=BUTTON_CLICKED_BACKGROUND_COLOR, activeforeground=BUTTON_CLICKED_TEXT_COLOR,relief=RIDGE,bd=0)
    set_button.place(x=150,y=600,width=200,height=50)

    back_button = Button(userInfoPage,text="Back",command=setActiveScreenMain,fg=TEXT_ORANGE_COLOR,bg=BUTTON_BACKGROUND_COLOR,font="Courier",activebackground=BUTTON_CLICKED_BACKGROUND_COLOR, activeforeground=BUTTON_CLICKED_TEXT_COLOR,relief=RIDGE,bd=0)
    back_button.place(x=150,y=700,width=200,height=50)


setActiveScreenStart()

window.mainloop()

exit()
