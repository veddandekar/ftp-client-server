import socket
import threading


end = False


def chat_receive():
    while not end:
        msg = s.recv(4096)
        print(msg.decode("ASCII"))


def chat_send():
    global end
    while not end:
        inpt = input()
        inpt = inpt + '\r\n'
        #if not inpt:
            #inpt="\n"
        s.send(inpt.encode("ASCII"))
        if inpt == "QUIT\r\n":
            end = True


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
