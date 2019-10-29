#! /usr/bin/python3
import socket
import threading
import os
import random
import sys
import getpass
import glob


class comm_sock:
    def __init__(self, server, host):
        self.name = host
        self.end = False
        self.s = server
        self.msg = ""
        self.passive = True
        self.ascii = True
        self.server_rcv()
        if self.msg[:3] == '220':
            name = input('Name(' + self.name + ':' + getpass.getuser() + '): ')
            if not name:
                name = getpass.getuser()
            self.s.send(("USER " + name + "\r\n").encode('ascii'))
            self.server_rcv()
            if self.msg[:3] == '331':
                password = getpass.getpass()
                self.s.send(("PASS " + password + "\r\n").encode('ascii'))
                self.server_rcv()
                if not self.msg[:3] == '230':
                    print("Login failed.")
                    self.end = True
                    return
        send_thread = threading.Thread(target=self.cmd_process)
        send_thread.start()
        send_thread.join()

    def server_rcv(self):
        a = ""
        self.msg = ""
        while a != "\r":
            a = self.s.recv(1).decode('ascii')
            if not a:
                print("Server Dsiconnected")
                sys.exit(0)
            self.msg = self.msg + a
        print(self.msg)
        self.s.recv(1).decode('ascii')

    def data_rcv(self, file=None, NLST=False):
        success = True
        data = ""
        if not file:
            while success:
                try:
                    chunk = self.data_server.recv(4096).decode('ascii')
                    chunk = chunk.replace("\r\n", "\n")
                    success = False
                except:
                    continue
            while chunk:
                data = data + chunk
                chunk = self.data_server.recv(4096).decode('ascii')
                chunk = chunk.replace("\r\n", "\n")
            if not NLST:
                print(data, end='')
            else:
                self.nlst_data = data
        else:
            if not self.ascii:
                while success:
                    try:
                        chunk = self.data_server.recv(4096)
                        success = False
                    except:
                        continue
                f = open(os.getcwd() + "/" + file, "wb")
                while chunk:
                    f.write(chunk)
                    chunk = self.data_server.recv(4096)
                f.close()
            else:
                while success:
                    try:
                        chunk = self.data_server.recv(4096).decode('ascii')
                        chunk = chunk.replace("\r\n", "\n")
                        success = False
                    except:
                        continue
                f = open(os.getcwd() + "/" + file, "w")
                while chunk:
                    f.write(chunk)
                    chunk = self.data_server.recv(4096).decode('ascii')
                    chunk = chunk.replace("\r\n", "\n")
                f.close()
            print(str(os.path.getsize(os.getcwd() + "/" + file)) + " bytes received.")
        self.data_server.close()

    def data_send(self, file):
        if not self.ascii:
            f = open(os.getcwd() + "/" + file, "rb")
            chunk = f.read(4096)
            while chunk:
                self.data_server.send(chunk)
                chunk = f.read(4096)
        else:
            f = open(os.getcwd() + "/" + file, "r")
            try:
                testChunk = f.read(4096)
            except:
                print("Error reading file, try sending in binary mode.")
                f.close()
                self.data_server.close()
                return
            f.seek(0, 0)
            chunk = f.read(4096)
            chunk = chunk.replace("\n", "\r\n")
            while chunk:
                self.data_server.send(chunk.encode('ascii'))
                chunk = f.read(4096)
                chunk = chunk.replace("\n", "\r\n")

        f.close()
        print(str(os.path.getsize(os.getcwd() + "/" + file)) + " bytes sent.")
        self.data_server.close()


    def data_sock(self, datasocket):
        self.data_server, data_addr = datasocket.accept()
        print("Data connection established")


    def active_conn(self):
        global ip
        port = random.randint(1024, 65535)
        a1, a2, a3, a4 = ip.split(".")
        datasocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        datasocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        datasocket.bind((ip, port))
        datasocket.listen(1)
        data_thread = threading.Thread(target=self.data_sock, args=(datasocket,))
        data_thread.daemon = True
        data_thread.start()
        self.s.send(("PORT " + a1 + "," + a2 + "," + a3 + "," + a4 + "," + str(int(port/256)) + "," + str(int(port%256)) + "\r\n").encode('ascii'))
        self.server_rcv()
        return self.msg[:3]


    def passive_conn(self):
        self.s.send("PASV\r\n".encode("ascii"))
        self.server_rcv()
        if self.msg[:3] == "227":
            l = self.msg.split("(")
            a1, a2, a3, a4, p1, p2 = l[1].split(",")
            p2 = p2.split(")")[0]
            self.data_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            host = a1 + '.' + a2 + '.' + a3 + '.' + a4
            port = int(p1) * 256 + int(p2)
            self.data_server.connect((host, port))
            return "227"
        return "425"


    def cmd_process(self):
        while not self.end:
            inpt = input("ftp> ")
            if not inpt:
                continue
            if self.end:
                return
            if inpt[0] == '!':
                if inpt[1:3] == "cd":
                    arg = inpt.split(" ")
                    os.chdir(arg[1])
                else:
                    os.system(inpt[1:])

            elif inpt == "passive":
                self.passive = not self.passive
                print("Passive: " + str(self.passive))

            elif inpt == "ls" or inpt == "dir":
                if self.passive:
                    if self.passive_conn() == "227":
                        self.ascii = True
                        self.s.send("TYPE A\r\n".encode("ascii"))
                        self.server_rcv()
                        if self.msg[:3] == '200':
                            self.s.send("LIST\r\n".encode("ascii"))
                            self.server_rcv()
                            if self.msg[:3] == "150":
                                self.data_rcv()
                                self.server_rcv()
                else:
                    if self.active_conn() == "200":
                        self.ascii = True
                        self.s.send("TYPE A\r\n".encode("ascii"))
                        self.server_rcv()
                        if self.msg[:3] == '200':
                            self.s.send("LIST\r\n".encode("ascii"))
                            self.server_rcv()
                            if self.msg[:3] == "150":
                                self.data_rcv()
                                self.server_rcv()

            elif inpt[:6] == "rename":
                arg = inpt.split(" ")
                if len(arg) == 1:  # NEW
                    arg_from = input("from-name: ")
                    arg_to = input("to-name: ")
                elif len(arg) == 2:
                    arg_from = arg[1]
                    arg_to = input("to-name: ")
                else:
                    arg_from = arg[1]
                    arg_to = arg[2]
                self.s.send(("RNFR " + arg_from + "\r\n").encode("ascii"))
                self.server_rcv()
                if self.msg[:3] == "350":
                    self.s.send(("RNTO " + arg_to + "\r\n").encode("ascii"))
                    self.server_rcv()

            elif inpt[:3] == "pwd":
                self.s.send("PWD\r\n".encode('ascii'))
                self.server_rcv()

            elif inpt[:4] == "cdup":
                self.s.send("CDUP\r\n".encode('ascii'))
                self.server_rcv()

            elif inpt[:2] == "cd":
                arg = inpt.split(" ")
                if len(arg) == 1:
                    dir = input("(remote-directory): ")
                    if not dir:
                        print("Invalid usage.")
                    else:
                        self.s.send(("CWD " + dir + "\r\n").encode('ascii'))
                        self.server_rcv()
                else:
                    dir = arg[1]
                    self.s.send(("CWD " + dir + "\r\n").encode('ascii'))
                    self.server_rcv()


            elif inpt[:5] == "mkdir":
                arg = inpt.split(" ")
                if len(arg) == 1:
                    dir = input("(remote-directory): ")
                    if not dir:
                        print("Invalid usage.")
                    else:
                        self.s.send(("MKD " + dir + "\r\n").encode('ascii'))
                        self.server_rcv()
                else:
                    dir = arg[1]
                    self.s.send(("MKD " + dir + "\r\n").encode('ascii'))
                    self.server_rcv()

            elif inpt[:5] == "rmdir":
                arg = inpt.split(" ")
                if len(arg) == 1:
                    dir = input("(remote-directory): ")
                    if not dir:
                        print("Invalid usage.")
                    else:
                        self.s.send(("RMD " + dir + "\r\n").encode('ascii'))
                        self.server_rcv()
                else:
                    dir = arg[1]
                    self.s.send(("RMD " + dir + "\r\n").encode('ascii'))
                    self.server_rcv()


            elif inpt[:6] == "delete":
                arg = inpt.split(" ")
                if len(arg) == 1:
                    dir = input("(remote-file): ")
                    if not dir:
                        print("Invalid usage.")
                    else:
                        self.s.send(("DELE " + dir + "\r\n").encode('ascii'))
                        self.server_rcv()
                else:
                    dir = arg[1]
                    self.s.send(("DELE " + dir + "\r\n").encode('ascii'))
                    self.server_rcv()
                    

            elif inpt[:5] == "chmod":
                arg = inpt.split(" ")
                if len(arg) == 1:  # NEW
                    mode = input("mode: ")
                    fname = input("file-name: ")
                elif len(arg) == 2:
                    mode = arg[1]
                    fname = input("file-name: ")
                else:
                    mode = arg[1]
                    fname = arg[2]
                self.s.send(("SITE CHMOD " + mode + " " + fname + "\r\n").encode("ascii"))
                self.server_rcv()
                
                
            elif inpt == "ascii":
                self.s.send(("TYPE A\r\n").encode('ascii'))
                self.server_rcv()
                self.ascii = True

            elif inpt == "binary" or inpt == "image":
                self.s.send(("TYPE I\r\n").encode('ascii'))
                self.server_rcv()
                self.ascii = False

            elif inpt == "exit" or inpt == "disconnect" or inpt == "quit":
                self.s.send(("QUIT\r\n").encode('ascii'))
                self.server_rcv()
                self.end = True

            elif inpt[:3] == "get":
                arg = inpt.split(" ")
                if len(arg) == 1:
                    arg = input("(remote-file): ")
                    fname = input("(local-file): ")
                    if not (arg or fname):
                        print("Invalid usage.")
                        continue
                elif len(arg) == 2:
                    fname = arg[1]
                    arg = arg[1]
                else:
                    fname = arg[2]
                    arg = arg[1]

                if self.passive:
                    if self.passive_conn() == "227":
                        data_thread = threading.Thread(target=self.data_rcv, args=(fname, ))
                        self.s.send(("RETR " + arg + "\r\n").encode("ascii"))
                        self.server_rcv()
                        data_thread.start()
                        if self.msg[:3] == '150':
                            data_thread.join()
                else:
                    if self.active_conn() == "200":
                        data_thread = threading.Thread(target=self.data_rcv, args=(fname, ))
                        data_thread.daemon = True
                        self.s.send(("RETR " + arg + "\r\n").encode("ascii"))
                        self.server_rcv()
                        data_thread.start()
                        if self.msg[:3] == '150':
                            data_thread.join()
                self.server_rcv()

            elif inpt[:4] == "mget":
                mode = self.ascii
                arg = inpt.split(" ")
                if len(arg) == 1:
                    arg = input("(remote-files): ").split(" ")
                    if not arg:
                        print("Invalid usage.")
                        continue
                else:
                    arg = inpt[5:].split(" ")
                for fname in arg:
                    if self.passive:
                        if self.passive_conn() == "227":
                            if not self.ascii:
                                self.ascii = True
                                self.s.send("TYPE A\r\n".encode("ascii"))
                                self.server_rcv()
                            self.s.send(("NLST " + fname + "\r\n").encode("ascii"))
                            self.server_rcv()
                            self.data_rcv(None, True)
                            l = self.nlst_data.split("\n")
                            if not mode:
                                self.ascii = False
                                self.s.send("TYPE I\r\n".encode("ascii"))
                                self.server_rcv()
                            for item in l:
                                item = item.strip()
                                if(input("mget " + item + "?") == 'y'):
                                    data_thread = threading.Thread(target=self.data_rcv, args=(item, ))
                                    self.passive_conn()
                                    self.s.send(("RETR " + item + "\r\n").encode("ascii"))
                                    self.server_rcv()
                                    data_thread.start()
                                    if self.msg[:3] == '150':
                                        data_thread.join()
                                        self.server_rcv()
                    else:
                        if self.active_conn() == "200":
                            if not self.ascii:
                                self.ascii = True
                                self.s.send("TYPE A\r\n".encode("ascii"))
                                self.server_rcv()
                            self.s.send(("NLST " + fname + "\r\n").encode("ascii"))
                            self.server_rcv()
                            self.data_rcv(None, True)
                            l = self.nlst_data.split("\r\n")
                            if not mode:
                                self.ascii = False
                                self.s.send("TYPE I\r\n".encode("ascii"))
                                self.server_rcv()
                            for item in l:
                                if(input("mget " + item + "?") == 'y'):
                                    data_thread = threading.Thread(target=self.data_rcv, args=(item, ))
                                    data_thread.daemon = True
                                    self.active_conn()
                                    self.s.send(("RETR " + item + "\r\n").encode("ascii"))
                                    self.server_rcv()
                                    data_thread.start()
                                    if self.msg[:3] == '150':
                                        data_thread.join()
                                        self.server_rcv()

            elif inpt[:3] == "put":
                arg = inpt.split(" ")
                if len(arg) == 1:
                    arg = input("(local-file): ")
                    fname = input("(remote-file): ")
                    if not (arg or fname):
                        print("Invalid usage.")
                        continue
                elif len(arg) == 2:
                    fname = arg[1]
                    arg = arg[1]
                else:
                    fname = arg[2]
                    arg = arg[1]
                if not os.path.isfile(os.path.join(os.getcwd(), arg)):
                    print("No such file or directory")
                else:
                    if self.passive:
                        if self.passive_conn() == "227":
                            data_thread = threading.Thread(target=self.data_send, args=(arg, ))
                            self.s.send(("STOR " + fname + "\r\n").encode("ascii"))
                            self.server_rcv()
                            data_thread.start()
                            if self.msg[:3] == '150':
                                data_thread.join()
                    else:
                        if self.active_conn() == "200":
                            data_thread = threading.Thread(target=self.data_send, args=(arg, ))
                            data_thread.daemon = True
                            self.s.send(("STOR " + fname + "\r\n").encode("ascii"))
                            self.server_rcv()
                            data_thread.start()
                            if self.msg[:3] == '150':
                                data_thread.join()
                    self.server_rcv()

            elif inpt[:4] == "mput":
                arg = inpt.split(" ")
                if len(arg) == 1:
                    arg = input("(local-files): ").split(" ")
                    if not arg:
                        print("Invalid usage.")
                        continue
                else:
                    arg = inpt[5:].split(" ")

                for each in arg:
                    flist = glob.glob(each)
                    for fname in flist:
                        if not os.path.isfile(os.path.join(os.getcwd(), fname)):
                            print("No such file or directory")
                        else:
                            if input("mput " + fname + "?") == "y":
                                if self.passive:
                                    if self.passive_conn() == "227":
                                        data_thread = threading.Thread(target=self.data_send, args=(fname, ))
                                        self.s.send(("STOR " + fname + "\r\n").encode("ascii"))
                                        self.server_rcv()
                                        data_thread.start()
                                        if self.msg[:3] == '150':
                                            data_thread.join()
                                else:
                                    if self.active_conn() == "200":
                                        data_thread = threading.Thread(target=self.data_send, args=(fname, ))
                                        data_thread.daemon = True
                                        self.s.send(("STOR " + fname + "\r\n").encode("ascii"))
                                        self.server_rcv()
                                        data_thread.start()
                                        if self.msg[:3] == '150':
                                            data_thread.join()
                                self.server_rcv()

            else:
                print("?Invalid command.")


if __name__ == "__main__":
    global ip
    if len(sys.argv) == 2:
        host = sys.argv[1]
        ip = socket.gethostname()
        ip = socket.gethostbyname(ip)
        port = 21
    elif len(sys.argv) == 3:
        host = sys.argv[1]
        port = int(sys.argv[2])
        ip = socket.gethostname()
        ip = socket.gethostbyname(ip)
    else:
        host = input("Enter IP: ")
        ip = input("Enter IP to bind to: ")
        try:
            port = int(input("Enter Port: "))
        except:
            port = 21
    host = socket.gethostbyname(host)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Trying "+ host)
    try:
        s.connect((host, port))
    except:
        print("Connection Refused.")
        sys.exit()
    print("Connected to " + host + ":" + str(port))
    comm_sock(s, host)
    s.close()
