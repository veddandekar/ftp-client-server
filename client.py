import socket
import threading

class comm_sock:
    def __init__(self, server):
        self.end = False
        self.rcvstatus = False
        self.s = server
        self.msg = ""
        self.passive = True
        send_thread = threading.Thread(target=self.cmd_process)
        send_thread.start()
        rcv_thread = threading.Thread(target=self.cmd_rcv)
        rcv_thread.start()
        send_thread.join()

    def data_rcv(self, data_conn):              #FILE RECEIVE AND LS RECEIVE SAME FUNCTION?????
        data = data_conn.recv(4096).decode('ascii')
        print(data)
        data_conn.close()

    def cmd_rcv(self):
        while not self.end:
            self.msg = self.s.recv(4096).decode('ascii')
            self.rcvstatus = True
            print(self.msg)


    def cmd_process(self):
        while not self.end:
            inpt = input()

            if inpt == "passive":
                self.passive = not self.passive
                print("Passive: " + self.passive)

            elif inpt == "ls":
                if self.passive:                                    #handle for else active
                    self.s.send("PASV\r\n".encode("ascii"))
                    self.rcvstatus = False
                    while not self.rcvstatus:
                        pass
                    if self.msg[:3] == "227":
                        l = self.msg.split("(")
                        a1, a2, a3, a4, p1, p2 = l[1].split(",")
                        p2 = p2.split(")")[0]
                        data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        host = a1 + '.' + a2 + '.' + a3 + '.' + a4
                        port = int(p1) * 256 + int(p2)
                        data_sock.connect((host, port))
                        data_thread = threading.Thread(target=self.data_rcv, args=(data_sock,))
                        data_thread.start()
                        self.s.send("LIST\r\n".encode("ascii"))
                        data_thread.join()

            elif inpt[:6] == "rename":              #Implement diff ways to use this command
                arg, arg_from, arg_to = inpt.split(" ")
                self.s.send(("RNFR " + arg_from + "\r\n").encode("ascii"))
                self.rcvstatus = False
                while not self.rcvstatus:
                    pass
                if self.msg[:3] == "350":
                    self.s.send(("RNTO " + arg_to + "\r\n").encode("ascii"))

            elif inpt[:3] == "get":
                arg = inpt[4:].strip()
                self.s.send("PASV\r\n".encode("ascii"))
                self.rcvstatus = False
                while not self.rcvstatus:
                    pass
                if self.msg[:3] == "227":
                    l = self.msg.split("(")
                    a1, a2, a3, a4, p1, p2 = l[1].split(",")
                    p2 = p2.split(")")[0]
                    data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    host = a1 + '.' + a2 + '.' + a3 + '.' + a4
                    port = int(p1) * 256 + int(p2)
                    data_sock.connect((host, port))
                    data_thread = threading.Thread(target=self.data_rcv, args=(data_sock,))
                    data_thread.start()
                    self.s.send("RETR " + arg + "\r\n".encode("ascii"))
                    data_thread.join()


            else:
                inpt = inpt + '\r\n'
                self.s.send(inpt.encode("ascii"))
                self.rcvstatus = False

            if inpt == "QUIT\r\n":                              #bye and close also do the exact same
                self.end = True

if __name__ == "__main__":
    host = input("Enter IP: ")
    port = int(input("Enter Port: "))

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))                                     #Error handling
    comm_sock(s)
    s.close()
