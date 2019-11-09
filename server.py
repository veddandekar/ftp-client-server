#! /usr/bin/python3
import socket
import threading
import os
import sys
import random
import shutil
import platform
import glob
import subprocess


class comm_sock:
    def __init__(self, client, addr):                                                                                   #Initialize class variables and call authenticate
        self.name = addr
        self.authenticated = False
        if platform.system() != "Windows":
            client.send("220 (ChiaVedu 1.0)\r\n".encode('ascii'))
            if self.authenticate(client):
                client.send("230 login successful.\nUsing ASCII mode to tranfer files.\r\n".encode('ascii'))
                self.authenticated = True
            else:
                client.send("530 Login incorrect.\r\n".encode('ascii'))
                return
        else:
            client.send("(ChiaVedu 1.0)\nAuthentication not supported on Windows\r\n".encode('ascii'))
            self.authenticated = True
        self.client = client
        self.ascii = True
        self.passive = True
        self.dirpath = os.path.expanduser("~")                          #Set directory to user's home directory
        self.offset = 0
        os.chdir(self.dirpath)
        self.cmd_process()
        return

    def authenticate(self, client):                                     #Authenticate client
        msg = client.recv(1024).decode('ascii')
        if not msg:
            print(self.name, " has lost connection.")
            return False
        if msg[:4] == "USER":
            user = msg[5:].strip()
            client.send("331 Please specify the password.\r\n".encode("ascii"))
            msg = client.recv(1024).decode('ascii')
            if msg[:4] == "PASS":
                password = msg[5:].strip()
            else:
                print(self.name, "has lost connection.")
                return False
            if user == "anonymous":
                return True
        return pam.pam().authenticate(user, password)                   #Matches provided user and password with system user and password


    def reply(self, msg):                                               #Sends control message reply to client
        self.client.send((msg + "\r\n").encode('ascii'))


    def data_send(self, data):                                          #Sends data to client
        if not self.ascii:                                              #Binary mode
            self.data_client.send(data)
        else:                                                           #ASCII mode
            data = data.replace("\n", "\r\n")
            self.data_client.send(data.encode('ascii'))


    def data_receive(self, file):                                       #Receive data from client
        data = ""
        if not self.ascii:                                              #Binary mode
            chunk = self.data_client.recv(1024)
            f = open(os.path.join(self.dirpath, file), "wb")
            while chunk:
                f.write(chunk)
                chunk = self.data_client.recv(1024)
        else:                                                           #ASCII mode
            chunk = self.data_client.recv(1024).decode('ascii')
            chunk = chunk.replace("\r\n", "\n")

            f = open(os.path.join(self.dirpath, file), "w")
            while chunk:
                f.write(chunk)
                chunk = self.data_client.recv(1024).decode('ascii')
                chunk = chunk.replace("\r\n", "\n")

        f.close()
        self.data_client.close()


    def data_sock(self, datasocket):                                    #Accepts data connection from client
        self.data_client, data_addr = datasocket.accept()


    def cmd_process(self):                                              #Processes received commands
        global ip

        while True:
            msg = self.client.recv(1024).decode('ascii')

            if not msg:                                                 #Checks if client connection has been lost
                self.client.close()
                print(self.name, " has lost connection.")
                return

            if not self.authenticated:
                self.reply("530 Please login with USER and PASS.")
            elif msg[:4] == "LIST":                                       #For ls
                arg = msg.strip().split(" ")
                if len(arg) == 2:
                    arg = arg[1]
                else:
                    arg = ""
                self.reply("150 Here comes the directory listing.")

                if platform.system() != "Windows":                                                     #If not Linux/Mac, run "ls -la"
                    reply_msg = subprocess.check_output('ls -l ' + arg, shell=True).decode("utf-8")
                    reply_msg = reply_msg.replace("\n", "\r\n")
                else:                                                                                   #If Windows, run "dir"
                    reply_msg =  subprocess.check_output('dir ' + arg, shell=True).decode("utf-8")          #CHECK

                self.data_send(reply_msg)
                self.data_client.close()
                self.reply("226 Directory send OK.")

            elif msg == "PWD\r\n":                                      #For pwd
                reply_msg = "257 \"" + self.dirpath + "\" is the current directory."
                self.reply(reply_msg)

            elif msg == "CDUP\r\n":                                     #For cdup
                os.chdir(self.dirpath)
                os.chdir(os.path.abspath('..'))                         #Switch to parent dir
                self.dirpath = os.getcwd()
                self.reply("250 Directory successfully changed to \"" + self.dirpath + "\"")

            elif msg[:3] == "CWD":                                      #For cd
                arg = msg[4:].strip()

                if not arg:                                             #Missing arguments
                    self.reply("550 Failed to change directory.")

                else:                                                   #Change to specified directory
                    try:
                        os.chdir(arg)
                        self.dirpath = os.getcwd()
                        self.reply("250 Directory successfully changed to \"" + self.dirpath + "\"")
                    except:
                        self.reply("550 Failed to change directory.")

            elif msg[:3] == "MKD":                                      #For mkdir
                arg = msg[4:].strip()
                try:                                                        #mkdir in specified directory
                    os.mkdir(arg)
                    self.reply("257 \"" + os.path.join(self.dirpath, arg) + "\" created.")
                except:
                    self.reply("550 Create directory operation failed.")

            elif msg[:3] == "RMD":                                      #For rmdir
                arg = msg[4:].strip()
                try:                                                        #rmdir in specified directory
                    shutil.rmtree(arg)
                    self.reply("250 remove directory operation successful")
                except:
                    self.reply("550 Remove directory operation failed.")

            elif msg[:4] == "DELE":                                     #for delete
                arg = msg[5:].strip()
                try:                                                        #delete specified file
                    os.remove(os.path.join(self.dirpath, arg))
                    self.reply("250 Delete operation successful.")
                except:
                    self.reply("550 Delete operation failed.")

            elif msg[:10] == "SITE CHMOD":                              #For chmod
                mode, fname = msg[11:].split(" ")
                try:
                    os.chmod(fname.strip(), int(mode, 8))
                    self.reply("250 SITE CHMOD command successful.")
                except:
                    self.reply("550 SITE CHMOD command failed.")
                    
            elif msg[:4] == "RNFR":                                     #For rename
                arg_from = msg[5:].strip()

                if os.path.isfile(os.path.join(self.dirpath, arg_from)):            #Check if file exists
                    self.reply("350 Ready for RNTO.")

                    msg = self.client.recv(1024).decode('ascii')

                    if msg[:4] == "RNTO":
                        arg_to = msg[5:].strip()
                        os.rename(os.path.join(self.dirpath, arg_from), os.path.join(self.dirpath, arg_to))
                        self.reply("250 Rename successful.")
                else:
                    self.reply("550 RNFR command failed.")

            elif msg[:4] == "REST":
                self.offset = int(msg[5:].strip())
                self.reply("350 Restart position accepted (" + str(self.offset) + ").")

            elif msg[:4] == "TYPE":
                if msg[5] == 'A':                                       #Switch to ASCII mode
                    self.ascii = True
                    self.reply("200 Switching to ASCII mode.")
                elif msg[5] == 'I':                                     #Switch to Binary mode
                    self.ascii = False
                    self.reply("200 Switching to Binary mode.")

            elif msg[:4] == "NLST":                                     #For NLST, lists all matching filenames
                self.reply("150 Here comes the directory listing.")
                rmsg = ""
                for each in glob.glob(msg[5:].strip()):
                    rmsg = rmsg + each + "\r\n"
                rmsg = rmsg[:-2]
                self.data_send(rmsg)
                self.data_client.close()
                self.reply("226 Directory send OK.")

            elif msg[:4] == "RETR":                                     #For get
                arg = msg[5:].strip()
                if os.path.isfile(os.path.join(self.dirpath, arg)):             #Check if file exists
                    if not self.ascii:                                          #Binary mode
                        f = open(os.path.join(self.dirpath, arg), "rb")
                    else:                                                       #ASCII mode
                        f = open(os.path.join(self.dirpath, arg), "r")
                    try:
                        testChunk = f.read(1024)                                #Check if file is readable
                    except:
                        self.data_client.close()
                        self.reply("550 Failed to open file. Try Binary Mode.")         #File read failure occurs
                        continue
                    if self.offset == 0:
                        f.seek(0, 0)
                    else:
                        f.seek(self.offset, 0)
                    self.offset = 0
                    self.reply("150 Opening data connection for " + arg + "(" + str(os.path.getsize(os.path.join(self.dirpath, arg))) + ")")

                    while True:
                        chunk = f.read(1024)
                        if not chunk:
                            break
                        self.data_send(chunk)
                    self.data_client.close()
                    self.reply("226 Transfer complete")
                else:
                    self.reply("550 Failed to open file.")

            elif msg == "PASV\r\n":                                                     #Start Passive mode connection
                port = random.randint(1024, 65535)                                      #Generate random port
                a1, a2, a3, a4 = ip.split(".")
                datasocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                datasocket.bind((ip, port))
                datasocket.listen(1)
                data_thread = threading.Thread(target=self.data_sock, args=(datasocket,))
                data_thread.start()                                                     #Start accepting on data connection
                self.reply("227 Entering Passive Mode (" + a1 + "," + a2 + "," + a3 + "," + a4 + "," + str(int(port/256)) + "," + str(int(port%256)) + ")")
                data_thread.join()                                                      #Wait for successful connection

            elif msg[:4] == "STOR":                                                     #For put
                file = msg[5:].strip()
                data_thread = threading.Thread(target=self.data_receive, args=(file,))
                data_thread.start()                                                     #Start receiving on data connection
                self.reply("150 OK to send data.")
                data_thread.join()                                                      #Wait for transfer to complete
                self.reply(("226 Transfer complete."))

            elif msg[:4] == "PORT":                                                     #For Active connection
                a1, a2, a3, a4, p1, p2 = msg[5:].split(",")
                self.data_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.data_client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.data_client.bind((ip, 20))
                host = a1 + '.' + a2 + '.' + a3 + '.' + a4
                port = int(p1) * 256 + int(p2)
                self.data_client.connect((host, port))                                  #Connect to received ip and port
                self.reply("200 PORT command succesful. Consider using passive mode")

            elif msg == "QUIT\r\n":                                 #For Client quit
                self.reply("Goodbye.")
                print(self.name, " disconnected.")
                self.client.close()
                break
        return


def listener(ip, port):
    global serversocket, end

    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)                  #Declare port as reusable
    serversocket.bind((ip, port))
    serversocket.listen(5)
    print("Server started. Waiting for client.")

    while True:
        client, addr = serversocket.accept()
        print("Received connection from ", addr)
        client_thread = threading.Thread(target=comm_sock, args=(client, addr))
        client_thread.daemon = True
        client_thread.start()                                                           #Start thread to server client

    serversocket.close()


if __name__ == "__main__":
    if platform.system() != "Windows":
        import pam
    if len(sys.argv) == 2:                                                              #Only IP given, assume 21 as default
        ip = sys.argv[1]
        port = 21
    elif len(sys.argv) == 3:                                                            #Both IP and port given
        ip = sys.argv[1]
        port = int(sys.argv[2])
    else:                                                                               #If neither given, ask user explicitly
        ip = input("Enter IP: ")
        port = int(input("Enter port: "))

    ip = socket.gethostbyname(ip)                                                       #Convert Hostnames to ip

    listener_thread = threading.Thread(target=listener, args=(ip, port))                #Thread to accept Client connections
    listener_thread.daemon = True
    listener_thread.start()

    inpt = ""

    while inpt != "quit" and inpt != "exit" and inpt != "bye":                          #Wait for exit command
        inpt = input()
    print("Server shutdown!")
    sys.exit()
