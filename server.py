import socket
import threading
import os
import sys
import pam
import random
class comm_sock:
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

    def data_sock(self, datasocket):
        data_client, data_addr = datasocket.accept()
        print("Data connection establishes")

    def cmd_process(self):
        while True:
            msg = self.client.recv(4096).decode('ascii')

            print(msg)                                          # debugging

            if msg == "LIST\r\n":                               # Directory and file colours
                reply_msg = ""
                for x in os.listdir(self.dirpath):
                    reply_msg = reply_msg + x + "\r\n"
                self.reply(reply_msg)

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