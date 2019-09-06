import socket
import threading


def chat_receive():
    while True:
        msg = s.recv(4096)
        print(msg.decode("ASCII"))


def chat_send():
    while True:
        inpt = input()
        inpt = inpt+'\n'
        if not inpt:
            inpt="\n"
        s.send(inpt.encode("ASCII"))


host = input("Enter IP: ")
port = int(input("Enter Port: "))

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((host, port))
send_thread = threading.Thread(target=chat_send)
send_thread.start()
receive_thread = threading.Thread(target=chat_receive)
receive_thread.start()
send_thread.join()
s.close()
