import socket
import threading
import os
import sys
import pam
import random
import shutil

class comm_sock:                                                            #os.path.isfile("/path/to/file") <-- use for error checking
    def __init__(self, client):
        # if not self.authenticate(client):
        #     client.send("Auth Failed").encode('ascii')
        #     return
        self.client = client
        self.dirpath = "/home"                                          #try for windows as well

        client_thread = threading.Thread(target=self.cmd_process)
        client_thread.start()


    def authenticate(self, client):                                         #Fix formatting
        client.send("username: ".encode('ascii'))
        msg = client.recv(4096).decode('ascii')
        if msg[:4] == "USER":
            user = msg[5:].strip()
            client.send("User okay".encode("ascii"))                      #331 USER OK

        client.send("password: ".encode('ascii'))
        msg = client.recv(4096).decode('ascii')
        if msg[:4] == "PASS":
            password = msg[5:].strip()
            client.send(password.encode("ascii") )
        return pam.pam().authenticate(user, password)


    def reply(self, msg):
        self.client.send(msg.encode('ascii'))

    def data_reply(self, data):
        self.data_client.send(data.encode('ascii'))

    def data_sock(self, datasocket):
        self.data_client, data_addr = datasocket.accept()
        print("Data connection established")


    def cmd_process(self):
        while True:
            msg = self.client.recv(4096).decode('ascii')

            print(msg)                                          # debugging

            if msg == "LIST\r\n":                               # Directory and file colours
                reply_msg = ""
                for x in os.listdir(self.dirpath):
                    reply_msg = reply_msg + x + "\r\n"
                if self.data_client:                            #HANDLE ELSE
                    self.data_reply(reply_msg)
                else:
                    print("NO CONNECTION TO SEND ON")

            elif msg == "PWD\r\n":
                reply_msg = self.dirpath + "\r\n"
                self.reply(reply_msg)

            elif msg == "CDUP\r\n":
                os.chdir(self.dirpath)
                os.chdir(os.path.abspath('..'))
                self.dirpath = os.getcwd()
                reply_msg = self.dirpath + "\r\n"
                self.reply(reply_msg)

            elif msg[:3] == "CWD":
                arg = msg[4:].strip()
                if arg[0] == "\\":
                    os.chdir(arg)
                    self.dirpath = os.getcwd()
                else:
                    os.chdir(os.path.join(self.dirpath, arg))        # Handle inexistent directories
                    self.dirpath = os.getcwd()
                self.reply(self.dirpath + "\r\n")

            elif msg[:3] == "MKD":
                arg = msg[4:].strip()
                if arg[0] == "\\":
                    os.mkdir(arg)

                else:
                    os.mkdir(os.path.join(self.dirpath, arg))        # Handle existent directories
                self.reply("Directory created\r\n")

            elif msg[:3] == "RMD":
                arg = msg[4:].strip()
                if arg[0] == "\\":
                    shutil.rmtree(arg)

                else:
                    shutil.rmtree(os.path.join(self.dirpath, arg))     # Handle inexistent directories
                self.reply("Directory Deleted\r\n")

            elif msg[:4] == "DELE":
                arg = msg[5:].strip()
                if arg[0] == "\\":
                    os.remove(arg)

                else:
                    os.remove(os.path.join(self.dirpath, arg))     # Handle inexistent directories
                self.reply("File Deleted\r\n")
            elif msg[:4] == "RNFR":
                arg_from = msg[5:].strip()

                if os.path.isfile(os.path.join(self.dirpath, arg_from)):         #handle else
                    self.reply("350 RFNR Accepted\r\n")
                msg = self.client.recv(4096).decode('ascii')

                if msg[:4] == "RNTO":
                    arg_to = msg[5:].strip()
                    os.rename(os.path.join(self.dirpath, arg_from), os.path.join(self.dirpath, arg_to))
                    self.reply("File renamed\r\n")

            elif msg == "PASV\r\n":
                port = random.randint(1024, 65535)
                ip = socket.gethostbyname("localhost")
                a1, a2, a3, a4 = ip.split(".")
                # print(a1, p2, p3, p4, port)
                datasocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                datasocket.bind(("localhost", port))
                datasocket.listen(1)
                data_thread = threading.Thread(target=self.data_sock, args=(datasocket,))
                data_thread.start()
                self.reply("227 Entering Passive Mode (" + a1 + ", " + a2 + ", " + a3 + ", " + a4 + ", " + str(int(port/256)) + ", " + str(int(port%256)) + ")")
                data_thread.join()

            elif msg == "QUIT\r\n":
                print("Goodbye!")
                self.client.close()
                break
        return


def listener():
    global serversocket, end
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind(("localhost", 2222))
    serversocket.listen(5)
    print("Waiting for client")
    while not end:
        client, addr = serversocket.accept()
        print("Received connection from ", addr)
        comm_sock(client)
    print("SERVER SOCKET CLOSED")
    serversocket.close()


if __name__ == "__main__":
    global end
    end = False
    listener_thread = threading.Thread(target=listener)
    listener_thread.start()
    # listener_thread.join()
    if input() == "q":
        end = True
        print("Server shutdown!")
        sys.exit()          #does not work :C
