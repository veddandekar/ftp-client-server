import socket
import threading

class comm_sock:
    def __init__(self, server):
        self.end = False
        self.rcvstatus = False
        self.s = server
        self.msg = ""
        send_thread = threading.Thread(target=self.cmd_send)
        send_thread.start()
        rcv_thread = threading.Thread(target=self.cmd_rcv)
        rcv_thread.start()

    def cmd_rcv(self):
        while not self.end:
            self.msg = self.s.recv(4096)
            self.rcvstatus = True
            print(self.msg.decode("ascii"))


    def cmd_send(self):
        while not self.end:
            inpt = input()
            if inpt == "ls":
                self.s.send("PASV\r\n".encode("ascii"))
                self.rcvstatus = False
                while not self.rcvstatus:
                    pass

                if self.msg[:3] == "227":
                    l = self.msg.split("(")
                    a1, a2, a3, a4, p1, p2 = l[1].split(",")
                    print(a1, a2, a3, a4, p1, p2)
            inpt = inpt + '\r\n'

            self.s.send(inpt.encode("ascii"))
            self.rcvstatus = False
            if inpt == "QUIT\r\n":
                self.end = True

if __name__ == "__main__":
    host = input("Enter IP: ")
    port = int(input("Enter Port: "))

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))                                     #Error handling
    comm_sock(s)
    s.close()
