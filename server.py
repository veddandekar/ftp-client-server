import socket
import threading
import os

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


def server():
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind(("localhost", 2132))
    serversocket.listen(5)

    print("Waiting for client")

    client, addr = serversocket.accept()
    return client


def reply(msg):
    s.send(msg.encode('ascii'))


def chat_receive():
    while True:
        if not s:
            print("CLIENT RIP")
            return
        msg = s.recv(4096).decode('ascii')

        print(msg)

        if msg == "LIST\r\n":                               # Directory and file colours
            reply_msg = ""
            for x in os.listdir(os.getcwd()):
                reply_msg = reply_msg + x + "\r\n"
            reply(reply_msg)

        elif msg == "PWD\r\n":
            reply_msg = os.getcwd() + "\r\n"
            reply(reply_msg)

        elif msg == "CDUP\r\n":
            os.chdir(os.path.abspath('..'))
            reply_msg = os.getcwd() + "\r\n"
            reply(reply_msg)

        elif msg[:3] == "CWD":
            arg = msg[4:].strip()
            if arg[0] == "\\":
                os.chdir(arg)
            else:
                os.chdir(os.path.join(os.getcwd(), arg))        # Handle inexistent directories
            reply(os.getcwd()+"\r\n")
        elif msg == "QUIT\r\n":
            break
    return


s = server()

receive_thread = threading.Thread(target=chat_receive)
receive_thread.start()
receive_thread.join()
s.close()
