import socket
import threading


end = False
rcvstatus = False


def chat_receive():
    global rcvstatus, end
    while not end:
        global msg
        msg = s.recv(4096)
        rcvstatus = True
        print(msg.decode("ascii"))


def chat_send():
    global end, rcvstate, msg
    while not end:
        inpt = input()
        if inpt == "ls":
            s.send("PASV\r\n".encode("ascii"))
            rcvstatus = False
            while not rcvstatus:
                pass

            if msg[:3] == "227":
                l = msg.split("(")
                a1, a2, a3, a4, p1, p2 = l[1].split(",")
                print(a1, a2, a3, a4, p1, p2)
        inpt = inpt + '\r\n'

        s.send(inpt.encode("ascii"))
        rcvstatus = False
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
