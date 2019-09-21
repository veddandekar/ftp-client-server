import socket
import threading
import os
import random
import sys


class comm_sock:
    def __init__(self, server):
        self.end = False
        self.rcvstatus = False
        self.s = server
        self.msg = ""
        self.passive = True
        self.ascii = False
        send_thread = threading.Thread(target=self.cmd_process)
        send_thread.start()
        rcv_thread = threading.Thread(target=self.cmd_rcv)
        rcv_thread.start()
        send_thread.join()

    def data_rcv(self, file=None):              #HOW TO HANDLE EOF? OS dependant? Not Really.
        data = ""
        if not file:
            chunk = self.data_server.recv(4096).decode('ascii')
            while chunk:
                data = data + chunk
                chunk = self.data_server.recv(4096).decode('ascii')
            print(data)
        else:
            if not self.ascii:
                f = open(os.getcwd() + "/" + file, "ba+")
                chunk = self.data_server.recv(4096)
                while chunk:
                    f.write(chunk)
                    chunk = self.data_server.recv(4096)
                f.close()
            else:
                f = open(os.getcwd() + "/" + file, "a+")
                chunk = self.data_server.recv(4096).decode('ascii')
                while chunk:
                    f.write(chunk)
                    chunk = self.data_server.recv(4096).decode('ascii')
                f.close()
        self.data_server.close()

    def data_send(self, file):
        f = open(os.getcwd() + "/" + file, "rb")
        chunk = f.read(4096)
        while chunk:
            self.data_server.send(chunk)
            chunk = f.read(4096)
        f.close()
        self.data_server.close()


    def data_sock(self, datasocket):
        self.data_server, data_addr = datasocket.accept()
        print("Data connection established")


    def cmd_rcv(self):
        while not self.end:
            self.msg = self.s.recv(4096).decode('ascii')
            self.rcvstatus = True
            print(self.msg)


    def active_conn(self):
        port = random.randint(1024, 65535)
        ip = socket.gethostbyname("localhost")
        a1, a2, a3, a4 = ip.split(".")
        datasocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        datasocket.bind(("localhost", port))
        datasocket.listen(1)
        data_thread = threading.Thread(target=self.data_sock, args=(datasocket,))
        data_thread.start()
        self.s.send(("PORT " + a1 + "," + a2 + "," + a3 + "," + a4 + "," + str(int(port/256)) + "," + str(int(port%256)) + "\r\n").encode('ascii'))
        self.rcvstatus = False
        data_thread.join()
        while not self.rcvstatus:
            pass
        return self.msg[:3]


    def passive_conn(self):
        self.s.send("PASV\r\n".encode("ascii"))
        self.rcvstatus = False
        while not self.rcvstatus:
            pass
        if self.msg[:3] == "227":
            l = self.msg.split("(")
            a1, a2, a3, a4, p1, p2 = l[1].split(",")
            p2 = p2.split(")")[0]
            self.data_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            host = a1 + '.' + a2 + '.' + a3 + '.' + a4
            port = int(p1) * 256 + int(p2)
            self.data_server.connect((host, port))
            return "227"
        return "1010"           #CHANGE TO CODE FOR FAILURE

    def cmd_process(self):
        while not self.end:
            inpt = input()

            if inpt == "passive":
                self.passive = not self.passive
                print("Passive: " + str(self.passive))

            elif inpt == "ls" or inpt == "dir":
                if self.passive:                                    #handle for else active
                    if self.passive_conn() == "227":
                        data_rcvthread = threading.Thread(target=self.data_rcv)
                        data_rcvthread.start()
                        self.s.send("TYPE A\r\n".encode("ascii"))
                        self.ascii = True
                        self.rcvstatus = False
                        while not self.rcvstatus:
                            pass
                        if self.msg[:3] == '200':
                            self.s.send("LIST\r\n".encode("ascii"))
                            data_rcvthread.join()
                else:
                    if self.active_conn() == "200":
                        self.s.send("TYPE A\r\n".encode("ascii"))
                        self.ascii = True
                        self.rcvstatus = False
                        while not self.rcvstatus:
                            pass
                        if self.msg[:3] == '200':
                            self.s.send("LIST\r\n".encode("ascii"))
                            self.data_rcv()


            elif inpt[:6] == "rename":              #Implement diff ways to use this command
                arg, arg_from, arg_to = inpt.split(" ")
                self.s.send(("RNFR " + arg_from + "\r\n").encode("ascii"))
                self.rcvstatus = False
                while not self.rcvstatus:
                    pass
                if self.msg[:3] == "350":
                    self.s.send(("RNTO " + arg_to + "\r\n").encode("ascii"))

            elif inpt[:3] == "pwd":
                self.s.send("PWD\r\n".encode('ascii'))

            elif inpt[:4] == "cdup":
                self.s.send("CDUP\r\n".encode('ascii'))

            elif inpt[:2] == "cd":
                self.s.send(("CWD " + inpt[3:] + "\r\n").encode('ascii'))

            elif inpt[:5] == "mkdir":
                self.s.send(("MKD " + inpt[6:] + "\r\n").encode('ascii'))

            elif inpt[:5] == "rmdir":
                self.s.send(("RMD " + inpt[6:] + "\r\n").encode('ascii'))

            elif inpt[:6] == "delete":
                self.s.send(("DELE " + inpt[7:] + "\r\n").encode('ascii'))

            elif inpt == "ascii":
                self.s.send(("TYPE A\r\n").encode('ascii'))

            elif inpt == "binary" or inpt == "image":
                self.s.send(("TYPE I\r\n").encode('ascii'))

            elif inpt == "exit":                                      #handle bye and close
                self.s.send(("QUIT\r\n").encode('ascii'))
                self.end = True

            elif inpt[:3] == "get":                                 #handle third argument
                arg = str(inpt[4:].strip())
                if self.passive:
                    if self.passive_conn() == "227":
                        data_thread = threading.Thread(target=self.data_rcv, args=(arg, ))
                        data_thread.start()
                        self.s.send(("RETR " + arg + "\r\n").encode("ascii"))
                        data_thread.join()
                else:
                    if self.active_conn() == "200":
                        data_thread = threading.Thread(target=self.data_rcv, args=(arg, ))
                        data_thread.start()
                        self.s.send(("RETR " + arg + "\r\n").encode("ascii"))
                        data_thread.join()

            elif inpt[:3] == "put":
                arg = str(inpt[4:].strip())
                if self.passive:
                    if self.passive_conn() == "227":
                        data_thread = threading.Thread(target=self.data_send, args=(arg, ))
                        data_thread.start()
                        self.s.send(("STOR " + arg + "\r\n").encode("ascii"))
                        data_thread.join()
                        print("FILE SENT SUCCESSFULLY")
                else:
                    if self.active_conn() == "200":
                        data_thread = threading.Thread(target=self.data_send, args=(arg, ))
                        data_thread.start()
                        self.s.send(("STOR " + arg + "\r\n").encode("ascii"))
                        data_thread.join()
                        print("FILE SENT SUCCESSFULLY")


            else:
                inpt = inpt + '\r\n'
                self.s.send(inpt.encode("ascii"))
                self.rcvstatus = False

if __name__ == "__main__":
    host = input("Enter IP: ")
    port = int(input("Enter Port: "))

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))                                     #Error handling
    comm_sock(s)
    s.close()
