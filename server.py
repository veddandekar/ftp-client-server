import socket
import threading
import os
import sys
import pam

# # pwd
# dirpath = os.getcwd()
# print("current directory is : " + dirpath)
#
# # cd pathname
# # direct = input()
# # dirpath = os.path.join(dirpath, direct)     #IMPLEMENT TRY CATCH
#
# # cd ..
# print(os.path.abspath('..'))    # LIMIT
#
# # ls
# print(os.listdir(dirpath))

class comm_sock:
    def __init__(self, client):
        if not self.authenticate(client):
            client.send("Auth Failed").encode('ascii')
            return
        self.client = client
        self.dirpath = "/home"
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

    def cmd_process(self):
        while True:
            msg = self.client.recv(4096).decode('ascii')

            print(msg)          #debugging

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
            elif msg == "QUIT\r\n":
                print("Goodbye!")
                self.client.close()
                break
        return

def listener():
    global serversocket
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind(("localhost", 1111))
    serversocket.listen(5)
    print("Waiting for client")
    while not end:
        client, addr = serversocket.accept()
        print("Received connection from ", addr)
        comm_sock(client)
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