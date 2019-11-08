#! /usr/bin/python3
import socket
import threading
import os
import random
import sys
import getpass
import glob


class comm_sock:
    def __init__(self, host=None, port=None):
        self.history = []
        self.histnum = -1
        self.histlinesize = []
        self.host = host
        self.port = port
        self.end = False
        self.msg = ""
        self.passive = True
        self.ascii = True
        self.s = None
        self.prompt = True
        self.authenticated = True
        self.offset = 0
        self.controller()

    def controller(self):
        try:
            self.cmd_process()
        except KeyboardInterrupt:
            print()
            self.controller()

    def make_connection(self):
        self.host = socket.gethostbyname(self.host)
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("Trying "+ self.host)
        try:
            self.s.connect((self.host, self.port))
            print("Connected to " + self.host + ":" + str(self.port))
            self.authenticate()
        except:
            print("Connection Refused.")

    def authenticate(self):
        self.server_rcv()
        if self.msg[:3] == '220':
            name = input('Name(' + self.host + ':' + getpass.getuser() + '): ')
            if not name:
                name = getpass.getuser()
            self.s.send(("USER " + name + "\r\n").encode('ascii'))
            self.server_rcv()
            if self.msg[:3] == '331':
                password = getpass.getpass()
                self.s.send(("PASS " + password + "\r\n").encode('ascii'))
                self.server_rcv()
                if self.msg[:3] == '230':
                    self.authenticated = True
                    return
                print("Login failed.")
                self.end = True
                return

    def takeInput(self, outpt):
        if outpt == None:
            outpt = "ftp> "
        print(outpt, end="", flush=True)
        result = ""
        while True:
            if os.name != 'nt':
                import termios
                fd = sys.stdin.fileno()

                oldterm = termios.tcgetattr(fd)
                newattr = termios.tcgetattr(fd)
                newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
                termios.tcsetattr(fd, termios.TCSANOW, newattr)

                try:
                    c = sys.stdin.read(1)
                except IOError:
                    pass
                finally:
                    termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
            else:
                import msvcrt
                c = msvcrt.getch()

            if c != '\n' and ord(c) != 13:
                if ord(c) == 27 or ord(c) == 224:
                    if os.name != 'nt':
                        c = c + sys.stdin.read(2)
                        upArrow = False
                        downArrow = False
                    else:
                        c = msvcrt.getch()
                        if ord(c) == 72:
                            upArrow = True
                            downArrow = False
                        elif ord(c) == 80:
                            upArrow = False
                            downArrow = True
                    if c == "\x1b[A" or upArrow:
                        print('\r{0}'.format(outpt + self.history[self.histnum]) + ' ' * 30 + '\b' * 30, end="")
                        result = self.history[self.histnum]
                        self.histnum = self.histnum - 1
                        if self.histnum == -1:
                            self.histnum = 0

                    elif c == "\x1b[B" or downArrow:
                        self.histnum = self.histnum + 1
                        if self.histnum == len(self.history):
                            self.histnum = self.histnum - 1
                        print('\r{0}'.format(outpt + self.history[self.histnum]) + ' ' * 30 + '\b' * 30, end="")
                        result = self.history[self.histnum]
                    c = ""
                elif c == '\x7f' or ord(c) == 8:
                    if result != "":
                        print('\b \b', end="", flush=True)
                        result = result[:-1]
                    continue
                else:
                    if os.name == 'nt':
                        result = result + c.decode("utf-8")
                        print(c.decode("utf-8"), end="", flush=True)
                    else:
                        result = result + c
                        print(c, end="", flush=True)
                    continue
            else:
                break
        print()
        return result

    def server_rcv(self):
        a = ""
        self.msg = ""
        while a != "\r":
            a = self.s.recv(1).decode('ascii')
            if not a:
                print("Server Disconnected.")
                self.end = True
                sys.exit(0)
            self.msg = self.msg + a
        print(self.msg)
        self.s.recv(1).decode('ascii')

    def data_rcv(self, file=None, NLST=False, append=False):
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
                print(data, end="")
            else:
                self.nlst_data = data
        else:
            if self.offset:
                if not os.path.isfile(os.path.join(os.getcwd(), file)):
                    print("Restart works only if local file already exists.")
                    self.offset = 0
                    self.data_server.close()
                    return
            if not self.ascii:
                while success:
                    try:
                        chunk = self.data_server.recv(4096)
                        success = False
                    except:
                        continue
                if append:
                    print("append")
                    f = open(os.path.join(os.getcwd(), file), "ab")            #FIX FOR WINDOWS
                else:
                    f = open(os.path.join(os.getcwd(), file), "wb")

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
                if append:
                    f = open(os.path.join(os.getcwd(), file), "a")            #FIX FOR WINDOWS
                else:
                    f = open(os.path.join(os.getcwd(), file), "w")
                while chunk:
                    f.write(chunk)
                    chunk = self.data_server.recv(4096).decode('ascii')
                    chunk = chunk.replace("\r\n", "\n")
                f.close()
            print(str(os.path.getsize(os.path.join(os.getcwd(), file))-int(self.offset)) + " bytes received.")
        self.offset = 0
        self.data_server.close()

    def data_send(self, file):

        if not self.ascii:
            f = open(os.path.join(os.getcwd(), file), "rb")
            if self.offset == 0:
                f.seek(0, 0)
            else:
                f.seek(self.offset, 0)
            chunk = f.read(4096)
            while chunk:
                self.data_server.send(chunk)
                chunk = f.read(4096)
        else:
            f = open(os.path.join(os.getcwd(), file), "r")

            try:
                testChunk = f.read(4096)
            except:
                print("Error reading file, try sending in binary mode.")
                f.close()
                self.data_server.close()
                return
            f.seek(0, 0)
            if self.offset == 0:
                f.seek(0, 0)
            else:
                f.seek(self.offset, 0)
            chunk = f.read(4096)
            chunk = chunk.replace("\n", "\r\n")
            while chunk:
                self.data_server.send(chunk.encode('ascii'))
                chunk = f.read(4096)
                chunk = chunk.replace("\n", "\r\n")

        f.close()
        self.offset = 0
        print(str(os.path.getsize(os.path.join(os.getcwd(), file))) + " bytes sent.")
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
                inpt = self.takeInput("ftp> ")
                self.history.append(inpt)
                self.histnum = len(self.history) - 1
                if not inpt:
                    continue
                if self.end:
                    return
                if inpt[:4] == "open":
                    args = inpt[5:].strip().split(" ")
                    self.ip = socket.gethostname()
                    self.ip = socket.gethostbyname(self.ip)
                    if len(args) == 1:
                        self.host = args[0]
                        self.port = 21
                    elif len(args) == 2:
                        self.host = args[0]
                        self.port = int(args[1])
                    self.make_connection()
                    continue

                elif inpt[0] == '!':
                    if inpt[1:3] == "cd":
                        arg = inpt.split(" ")
                        try:
                            os.chdir(arg[1])
                        except:
                            print("Invalid directory.")
                    else:
                        os.system(inpt[1:])

                elif inpt == "passive":
                    self.passive = not self.passive
                    print("Passive: " + str(self.passive))

                elif inpt == "prom" or inpt =="prompt":
                    self.prompt = not self.prompt
                    print("Interactive mode is " + str(self.prompt))

                elif inpt == "lcd":
                    print("Local directory now " + str(os.getcwd()))

                elif inpt == "exit" or inpt == "disconnect" or inpt == "quit":          #CHECK
                    if self.s:
                        self.s.send(("QUIT\r\n").encode('ascii'))
                        self.server_rcv()
                        self.s.close()
                        self.end = True
                    else:
                        print("Goodbye.")
                    return

                elif inpt[:2] == "ls" or inpt[:3] == "dir" or inpt[:4] == "mdir":
                    if not self.s:
                        print("Not connected.")
                        continue
                    # if not self.authenticated:
                    #     print("PLease login")
                    #     continue
                    l = inpt.strip().split(" ")
                    if l[0] == "ls" or l[0] == "dir":
                        l = l[:3]
                    l = l[1:]
                    if len(l) == 0:
                        filename = None
                        l = [""]
                    elif len(l) == 1:
                        filename = None
                    else:
                        filename = l[-1]
                        l = l[:-1]
                    if filename == "-":
                        filename = None
                    if filename:
                        if self.takeInput("Output to local-file: " + filename + "? ") != "y":
                            continue

                    loop = 0
                    for each in l:
                        if self.passive:
                            if self.passive_conn() == "227":
                                self.ascii = True
                                self.s.send("TYPE A\r\n".encode("ascii"))
                                self.server_rcv()
                                if self.msg[:3] == '200':
                                    self.s.send(("LIST " + each + "\r\n").encode("ascii"))
                                    self.server_rcv()
                                    if self.msg[:3] == "150":
                                        if loop == 0:
                                            self.data_rcv(filename)
                                        else:
                                            self.data_rcv(filename, append=True)
                                        self.server_rcv()
                        else:
                            if self.active_conn() == "200":
                                self.ascii = True
                                self.s.send("TYPE A\r\n".encode("ascii"))
                                self.server_rcv()
                                if self.msg[:3] == '200':
                                    self.s.send("LIST " + each + "\r\n".encode("ascii"))
                                    self.server_rcv()
                                    if self.msg[:3] == "150":
                                        if loop == 0:
                                            self.data_rcv(filename)
                                        else:
                                            self.data_rcv(filename, append=True)
                                        self.server_rcv()
                        loop = loop + 1

                elif inpt[:6] == "rename":
                    if not self.s:
                        print("Not connected.")
                        continue
                    arg = inpt.split(" ")
                    if len(arg) == 1:  # NEW
                        arg_from = self.takeInput("from-name: ")
                        arg_to = self.takeInput("to-name: ")
                    elif len(arg) == 2:
                        arg_from = arg[1]
                        arg_to = self.takeInput("to-name: ")
                    else:
                        arg_from = arg[1]
                        arg_to = arg[2]
                    self.s.send(("RNFR " + arg_from + "\r\n").encode("ascii"))
                    self.server_rcv()
                    if self.msg[:3] == "350":
                        self.s.send(("RNTO " + arg_to + "\r\n").encode("ascii"))
                        self.server_rcv()

                elif inpt[:3] == "pwd":
                    if not self.s:
                        print("Not connected.")
                        continue
                    self.s.send("PWD\r\n".encode('ascii'))
                    self.server_rcv()

                elif inpt[:4] == "cdup":
                    if not self.s:
                        print("Not connected.")
                        continue
                    self.s.send("CDUP\r\n".encode('ascii'))
                    self.server_rcv()

                elif inpt[:2] == "cd":
                    if not self.s:
                        print("Not connected.")
                        continue
                    arg = inpt.split(" ")
                    if len(arg) == 1:
                        dir = self.takeInput("(remote-directory): ")
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
                    if not self.s:
                        print("Not connected.")
                        continue
                    arg = inpt.split(" ")
                    if len(arg) == 1:
                        dir = self.takeInput("(remote-directory): ")
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
                    if not self.s:
                        print("Not connected.")
                        continue
                    arg = inpt.split(" ")
                    if len(arg) == 1:
                        dir = self.takeInput("(remote-directory): ")
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
                    if not self.s:
                        print("Not connected.")
                        continue
                    arg = inpt.split(" ")
                    if len(arg) == 1:
                        dir = self.takeInput("(remote-file): ")
                        if not dir:
                            print("Invalid usage.")
                        else:
                            self.s.send(("DELE " + dir + "\r\n").encode('ascii'))
                            self.server_rcv()
                    else:
                        dir = arg[1]
                        self.s.send(("DELE " + dir + "\r\n").encode('ascii'))
                        self.server_rcv()

                elif inpt[:7] == "restart":
                    if not self.s:
                        print("Not connected.")
                        continue
                    self.offset = int(inpt[8:])
                    print("restarting at " + str(self.offset) + ". execute get, put or append to initiate transfer")

                elif inpt[:5] == "reget":
                    if not self.s:
                        print("Not connected.")
                        continue
                    arg = inpt.split(" ")
                    if len(arg) == 1:
                        arg = self.takeInput("(remote-file): ")
                        fname = self.takeInput("(local-file): ")
                        if not (arg or fname):
                            print("Invalid usage.")
                            continue
                    elif len(arg) == 2:
                        fname = arg[1]
                        arg = arg[1]
                    else:
                        fname = arg[2]
                        arg = arg[1]

                    self.offset = int(os.path.getsize(os.path.join(os.getcwd(), arg)))

                    if self.passive:
                        if self.passive_conn() == "227":
                            if self.offset != 0:
                                self.s.send(("REST " + str(self.offset) + "\r\n").encode("ascii"))
                                self.server_rcv()
                                if self.msg[:3] != "350":
                                    continue
                            data_thread = threading.Thread(target=self.data_rcv, args=(fname, False, True))
                            self.s.send(("RETR " + arg + "\r\n").encode("ascii"))
                            self.server_rcv()
                            data_thread.start()
                            if self.msg[:3] == '150':
                                data_thread.join()
                                self.server_rcv()
                    else:
                        if self.active_conn() == "200":
                            if self.offset != 0:
                                self.s.send(("REST " + str(self.offset) + "\r\n").encode("ascii"))
                                self.server_rcv()
                                if self.msg[:3] != "350":
                                    continue
                            data_thread = threading.Thread(target=self.data_rcv, args=(fname,False, True))
                            data_thread.daemon = True
                            self.s.send(("RETR " + arg + "\r\n").encode("ascii"))
                            self.server_rcv()
                            data_thread.start()
                            if self.msg[:3] == '150':
                                data_thread.join()
                                self.server_rcv()

                elif inpt[:5] == "chmod":
                    if not self.s:
                        print("Not connected.")
                        continue
                    arg = inpt.split(" ")
                    if len(arg) == 1:  # NEW
                        mode = self.takeInput("mode: ")
                        fname = self.takeInput("file-name: ")
                    elif len(arg) == 2:
                        mode = arg[1]
                        fname = self.takeInput("file-name: ")
                    else:
                        mode = arg[1]
                        fname = arg[2]
                    self.s.send(("SITE CHMOD " + mode + " " + fname + "\r\n").encode("ascii"))
                    self.server_rcv()

                elif inpt == "ascii":
                    if not self.s:
                        print("Not connected.")
                        continue
                    self.s.send(("TYPE A\r\n").encode('ascii'))
                    self.server_rcv()
                    self.ascii = True

                elif inpt == "binary" or inpt == "image":
                    if not self.s:
                        print("Not connected.")
                        continue
                    self.s.send(("TYPE I\r\n").encode('ascii'))
                    self.server_rcv()
                    self.ascii = False

                elif inpt[:3] == "get":
                    if not self.s:
                        print("Not connected.")
                        continue
                    arg = inpt.split(" ")
                    if len(arg) == 1:
                        arg = self.takeInput("(remote-file): ")
                        fname = self.takeInput("(local-file): ")
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
                            if self.offset != 0:
                                self.s.send(("REST " + str(self.offset) + "\r\n").encode("ascii"))
                                self.server_rcv()
                                if self.msg[:3] != "350":
                                    continue
                            data_thread = threading.Thread(target=self.data_rcv, args=(fname, ))
                            self.s.send(("RETR " + arg + "\r\n").encode("ascii"))
                            self.server_rcv()
                            data_thread.start()
                            if self.msg[:3] == '150':
                                data_thread.join()
                                self.server_rcv()
                    else:
                        if self.active_conn() == "200":
                            if self.offset != 0:
                                self.s.send(("REST " + str(self.offset) + "\r\n").encode("ascii"))
                                self.server_rcv()
                                if self.msg[:3] != "350":
                                    continue
                            data_thread = threading.Thread(target=self.data_rcv, args=(fname, ))
                            data_thread.daemon = True
                            self.s.send(("RETR " + arg + "\r\n").encode("ascii"))
                            self.server_rcv()
                            data_thread.start()
                            if self.msg[:3] == '150':
                                data_thread.join()
                                self.server_rcv()

                elif inpt[:4] == "mget":
                    if not self.s:
                        print("Not connected.")
                        continue
                    mode = self.ascii
                    arg = inpt.split(" ")
                    if len(arg) == 1:
                        arg = self.takeInput("(remote-files): ").split(" ")
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
                                self.server_rcv()
                                l = self.nlst_data.split("\n")
                                l = l[:-1]                                  #CHECK IF AN EXTRA ITEM IS ALMOST GENERATED
                                if not mode:
                                    self.ascii = False
                                    self.s.send("TYPE I\r\n".encode("ascii"))
                                    self.server_rcv()
                                for item in l:
                                    item = item.strip()
                                    if(not self.prompt or self.takeInput("mget " + item + "?") == 'y'):
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
                                self.server_rcv()
                                l = self.nlst_data.split("\n")
                                l = l[:-1]
                                if not mode:
                                    self.ascii = False
                                    self.s.send("TYPE I\r\n".encode("ascii"))
                                    self.server_rcv()
                                for item in l:
                                    if(self.takeInput("mget " + item + "?") == 'y'):
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
                    if not self.s:
                        print("Not connected.")
                        continue
                    arg = inpt.split(" ")
                    if len(arg) == 1:
                        arg = self.takeInput("(local-file): ")
                        fname = self.takeInput("(remote-file): ")
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
                                if self.offset != 0:
                                    self.s.send(("REST " + str(self.offset) + "\r\n").encode("ascii"))
                                    self.server_rcv()
                                    if self.msg[:3] != "350":
                                        continue
                                data_thread = threading.Thread(target=self.data_send, args=(arg, ))
                                self.s.send(("STOR " + fname + "\r\n").encode("ascii"))
                                self.server_rcv()
                                data_thread.start()
                                if self.msg[:3] == '150':
                                    data_thread.join()
                        else:
                            if self.active_conn() == "200":
                                if self.offset != 0:
                                    self.s.send(("REST " + str(self.offset) + "\r\n").encode("ascii"))
                                    self.server_rcv()
                                    if self.msg[:3] != "350":
                                        continue
                                data_thread = threading.Thread(target=self.data_send, args=(arg, ))
                                data_thread.daemon = True
                                self.s.send(("STOR " + fname + "\r\n").encode("ascii"))
                                self.server_rcv()
                                data_thread.start()
                                if self.msg[:3] == '150':
                                    data_thread.join()
                        self.server_rcv()

                elif inpt[:4] == "mput":
                    if not self.s:
                        print("Not connected.")
                        continue
                    arg = inpt.split(" ")
                    if len(arg) == 1:
                        arg = self.takeInput("(local-files): ").split(" ")
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
                                if not self.prompt or self.takeInput("mput " + fname + "?") == "y":
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
    if len(sys.argv) == 1:
        comm_sock()
    elif len(sys.argv) == 2:
        host = sys.argv[1]
        ip = socket.gethostname()
        ip = socket.gethostbyname(ip)
        port = 21
        comm_sock(host, port)
    elif len(sys.argv) == 3:
        host = sys.argv[1]
        port = int(sys.argv[2])
        ip = socket.gethostname()
        ip = socket.gethostbyname(ip)
        comm_sock(host, port)
    else:
        print("Invalid arguments")
