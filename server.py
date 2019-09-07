import socket
import threading
import os
import sys
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
        self.client = client
        self.dirpath = "\\"
        client_thread = threading.Thread(target=self.cmd_process)
        client_thread.start()

    def reply(self, msg):
        self.client.send(msg.encode('ascii'))

    def cmd_process(self):
        while True:
            msg = self.client.recv(4096).decode('ascii')

            print(msg)          #debugging

            if msg == "LIST\r\n":                               # Directory and file colours
                reply_msg = ""
                for x in os.listdir(os.getcwd()):
                    reply_msg = reply_msg + x + "\r\n"
                self.reply(reply_msg)

            elif msg == "PWD\r\n":
                reply_msg = os.getcwd() + "\r\n"
                self.reply(reply_msg)

            elif msg == "CDUP\r\n":
                os.chdir(os.path.abspath('..'))
                reply_msg = os.getcwd() + "\r\n"
                self.reply(reply_msg)

            elif msg[:3] == "CWD":
                arg = msg[4:].strip()
                if arg[0] == "\\":
                    os.chdir(arg)
                else:
                    os.chdir(os.path.join(os.getcwd(), arg))        # Handle inexistent directories
                self.reply(os.getcwd()+"\r\n")
            elif msg == "QUIT\r\n":
                print("Goodbye!")
                self.client.close()
                break
        return

def listener():
    global serversocket
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind(("localhost", 2222))
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