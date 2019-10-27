#! /usr/bin/python3
import socket
import threading
import os
import sys
import pam
import random
import shutil
import platform
import glob
import subprocess


class comm_sock:
    def __init__(self, client, addr):
        self.name = addr
        if platform.system() != "Windows":
            client.send("220 (ChiaVedu 1.0)\r\n".encode('ascii'))
            if self.authenticate(client):
                client.send("230 login successful.\nUsing ASCII mode to tranfer files.\r\n".encode('ascii'))
            else:
                client.send("530 Login incorrect.\r\n".encode('ascii'))
                return
        else:
            client.send("(ChiaVedu 1.0)\r\n".encode('ascii'))
            client.send("Authentication not supported on Windows\r\n".encode("ascii"))
        self.client = client
        self.ascii = True
        self.passive = True
        self.dirpath = os.path.expanduser("~")
        self.cmd_process()
        return

    def authenticate(self, client):
        msg = client.recv(4096).decode('ascii')
        if not msg:
            print(self.name, " has lost connection.")
            return False
        if msg[:4] == "USER":
            user = msg[5:].strip()
            client.send("331 Please specify the password.\r\n".encode("ascii"))
            msg = client.recv(4096).decode('ascii')
            if msg[:4] == "PASS":
                password = msg[5:].strip()
            else:
                print(self.name, "has lost connection.")
                return False
        return pam.pam().authenticate(user, password)


    def reply(self, msg):
        self.client.send((msg + "\r\n").encode('ascii'))


    def data_send(self, data):
        if not self.ascii:
            self.data_client.send(data)
        else:
            data = data.replace("\n", "\r\n")
            self.data_client.send(data.encode('ascii'))


    def data_receive(self, file):
        data = ""
        if not self.ascii:
            chunk = self.data_client.recv(4096)
            f = open(os.path.join(self.dirpath, file), "wb")
            while chunk:
                f.write(chunk)
                chunk = self.data_client.recv(4096)
        else:
            chunk = self.data_client.recv(4096).decode('ascii')
            chunk = chunk.replace("\r\n", "\n")

            f = open(os.path.join(self.dirpath, file), "w")
            while chunk:
                f.write(chunk)
                chunk = self.data_client.recv(4096).decode('ascii')
                chunk = chunk.replace("\r\n", "\n")

        f.close()
        self.data_client.close()


    def data_sock(self, datasocket):
        self.data_client, data_addr = datasocket.accept()


    def cmd_process(self):
        global ip
        while True:
            msg = self.client.recv(4096).decode('ascii')
            if not msg:
                self.client.close()
                print(self.name, " has lost connection.")
                return

            if msg == "LIST\r\n":
                self.reply("150 Here comes the directory listing.")
                reply_msg = subprocess.check_output('ls -l', shell=True).decode("utf-8")
                reply_msg = reply_msg.replace("\n", "\r\n")
                # reply_msg = ""
                # for x in os.listdir(self.dirpath):
                #     reply_msg = reply_msg + x + "\r\n"
                self.data_send(reply_msg)
                self.data_client.close()
                self.reply("226 Directory send OK.")

            elif msg == "PWD\r\n":
                reply_msg = "257 \"" + self.dirpath + "\" is the current directory."
                self.reply(reply_msg)

            elif msg == "CDUP\r\n":
                os.chdir(self.dirpath)
                os.chdir(os.path.abspath('..'))
                self.dirpath = os.getcwd()
                self.reply("250 Directory successfully changed to \"" + self.dirpath + "\"")

            elif msg[:3] == "CWD":
                arg = msg[4:].strip()
                if not arg:
                    self.reply("550 Failed to change directory.")
                elif arg[0] == "\\":
                    try:
                        os.chdir(arg)
                        self.dirpath = os.getcwd()
                        self.reply("250 Directory successfully changed to \"" + self.dirpath + "\"")
                    except:
                        self.reply("550 Failed to change directory.")
                else:
                    try:
                        os.chdir(os.path.join(self.dirpath, arg))
                        self.dirpath = os.getcwd()
                        self.reply("250 Directory successfully changed to \"" + self.dirpath + "\"")
                    except:
                        self.reply("550 Failed to change directory.")
            elif msg[:3] == "MKD":
                arg = msg[4:].strip()
                if arg[0] == "\\":
                    try:
                        os.mkdir(arg)
                        self.reply("257 \"" + os.path.join(self.dirpath, arg) + "\" created.")
                    except:
                        self.reply("550 Create directory operation failed.")

                else:
                    try:
                        os.mkdir(os.path.join(self.dirpath, arg))
                        self.reply("257 \"" + os.path.join(self.dirpath, arg) + "\" created.")
                    except:
                        self.reply("550 Create directory operation failed.")

            elif msg[:3] == "RMD":
                arg = msg[4:].strip()
                if arg[0] == "\\":
                    try:
                        shutil.rmtree(arg)
                        self.reply("250 Remove directory operation successful")
                    except:
                        self.reply("550 Remove directory operation failed.")
                else:
                    try:
                        shutil.rmtree(os.path.join(self.dirpath, arg))
                        self.reply("250 remove directory operation successful")
                    except:
                        self.reply("550 Remove directory operation failed.")

            elif msg[:4] == "DELE":
                arg = msg[5:].strip()
                if arg[0] == "\\":
                    try:
                        os.remove(arg)
                        self.reply("250 Delete operation successful.")
                    except:
                        self.reply("550 Delete operation failed.")
                else:
                    try:
                        os.remove(os.path.join(self.dirpath, arg))
                        self.reply("250 Delete operation successful.")
                    except:
                        self.reply("550 Delete operation failed.")

            elif msg[:4] == "RNFR":
                arg_from = msg[5:].strip()

                if os.path.isfile(os.path.join(self.dirpath, arg_from)):
                    self.reply("350 Ready for RNTO.")

                    msg = self.client.recv(4096).decode('ascii')

                    if msg[:4] == "RNTO":
                        arg_to = msg[5:].strip()
                        os.rename(os.path.join(self.dirpath, arg_from), os.path.join(self.dirpath, arg_to))
                        self.reply("250 rename successful.")
                else:
                    self.reply("550 RNFR command failed.")

            elif msg[:4] == "TYPE":
                if msg[5] == 'A':
                    self.ascii = True
                    self.reply("200 Switching to ASCII mode.")
                elif msg[5] == 'I':
                    self.ascii = False
                    self.reply("200 Switching to Binary mode.")

            elif msg[:4] == "NLST":
                self.reply("150 Here comes the directory listing.")
                rmsg = ""
                for each in glob.glob(msg[5:].strip()):
                    rmsg = rmsg + each + "\r\n"
                rmsg = rmsg[:-2]
                self.data_send(rmsg)
                self.data_client.close()

            elif msg[:4] == "RETR":
                arg = msg[5:].strip()
                if os.path.isfile(os.path.join(self.dirpath, arg)):
                    if not self.ascii:
                        f = open(os.path.join(self.dirpath, arg), "rb")
                    else:
                        f = open(os.path.join(self.dirpath, arg), "r")
                    try:
                        testChunk = f.read(4096)
                    except:
                        self.data_client.close()
                        self.reply("550 Failed to open file.")
                        self.reply("550 Try Binary mode.")
                        continue
                    f.seek(0, 0)
                    self.reply("150 Opening data connection for " + arg + "(" + str(os.path.getsize(os.path.join(self.dirpath, arg))) + ")")
                    while True:
                        chunk = f.read(4096)
                        if not chunk:
                            break
                        self.data_send(chunk)
                    self.data_client.close()
                    self.reply("226 Transfer complete")
                else:
                    self.reply("550 Failed to open file.")
                    self.reply("550 Try Binary mode.")

            elif msg == "PASV\r\n":
                port = random.randint(1024, 65535)
                a1, a2, a3, a4 = ip.split(".")
                datasocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                datasocket.bind((ip, port))
                datasocket.listen(1)
                data_thread = threading.Thread(target=self.data_sock, args=(datasocket,))
                data_thread.start()
                self.reply("227 Entering Passive Mode (" + a1 + "," + a2 + "," + a3 + "," + a4 + "," + str(int(port/256)) + "," + str(int(port%256)) + ")")
                data_thread.join()

            elif msg[:4] == "STOR":
                file = msg[5:].strip()
                data_thread = threading.Thread(target=self.data_receive, args=(file,))
                data_thread.start()
                self.reply("150 OK to send data.")
                data_thread.join()
                self.reply(("226 Transfer complete."))

            elif msg[:4] == "PORT":
                a1, a2, a3, a4, p1, p2 = msg[5:].split(",")
                self.data_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.data_client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.data_client.bind((ip, 1212))
                host = a1 + '.' + a2 + '.' + a3 + '.' + a4
                port = int(p1) * 256 + int(p2)
                self.data_client.connect((host, port))
                self.reply("200 PORT command succesful. Consider using passive mode")

            elif msg == "QUIT\r\n":
                self.reply("Goodbye.")
                print(self.name, " disconnected.")
                self.client.close()
                break
        return


def listener(ip, port):
    global serversocket, end
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serversocket.bind((ip, port))
    serversocket.listen(5)
    print("Server started. Waiting for client.")
    while True:
        client, addr = serversocket.accept()
        print("Received connection from ", addr)
        client_thread = threading.Thread(target=comm_sock, args=(client, addr))
        client_thread.daemon = True
        client_thread.start()
    serversocket.close()


if __name__ == "__main__":
    if len(sys.argv) == 2:
        ip = sys.argv[1]
        port = 21
    elif len(sys.argv) == 3:
        ip = sys.argv[1]
        port = int(sys.argv[2])
    else:
        ip = input("Enter IP: ")
        port = int(input("Enter port: "))
    ip = socket.gethostbyname(ip)
    listener_thread = threading.Thread(target=listener, args=(ip, port))
    listener_thread.daemon = True
    listener_thread.start()
    inpt = ""
    while inpt != "quit" and inpt != "exit" and inpt != "bye":
        inpt = input()
    print("Server shutdown!")
    sys.exit()
