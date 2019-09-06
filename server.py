import socket
import threading
import os

#pwd
dirpath = os.getcwd()
print("current directory is : " + dirpath)

#cd pathname
# direct = input()
# dirpath = os.path.join(dirpath, direct)     #IMPLEMENT TRY CATCH

#cd ..
print(os.path.abspath('..'))    #LIMIT

#ls
print(os.listdir(dirpath))

def server():
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind(("localhost", 2871))
    serversocket.listen(5)

    print("Waiting for client")

    client, addr = serversocket.accept()
    return client


def chat_receive():
    while True:
        if not s:
            print("CLIENT RIP")
            return

        msg = s.recv(4096).decode('ascii')

        print(msg)

        if msg == "LIST\r\n":                       #Directory and file colours
            reply_msg = ""
            for x in os.listdir(dirpath):
                reply_msg = reply_msg + x + "\r\n"
            reply(reply_msg)


def reply(msg):
    s.send(msg.encode('ascii'))


s = server()

receive_thread = threading.Thread(target=chat_receive)
receive_thread.start()
receive_thread.join()
s.close()
