import socket
import threading
import json
import os

HOST = "127.0.0.1"
SERVER_PORT = 56700
FORMAT = "utf8"


class Client:
    def __init__(self):
        self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print("Client side")
        self.server_status = self.connect_server()

    def connect_server(self):
        try:
            self.soc.connect((HOST, SERVER_PORT))
            ipaddr, port = self.soc.getsockname()

            self.soc_alive = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.soc_alive.bind((ipaddr, port + 1))
            self.soc_alive.listen(1)

            print("client address:", ipaddr, ":", port)
            self.soc.send("CONNECT".encode())
            mess_from_server = self.soc.recv(1024).decode()
            print(mess_from_server)
            if mess_from_server == 'RESPONSE 200':
                return True
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    def signin_client(self):
        self.soc.send("SIGNIN".encode())
        mess_from_server = self.soc.recv(1024).decode()
        self.soc.send(input(mess_from_server).encode())
        mess_from_server = self.soc.recv(1024).decode()
        self.soc.send(input(mess_from_server).encode())

        mess_from_server = self.soc.recv(1024).decode()
        print(mess_from_server)
        if mess_from_server == "Login successful.":
            return True
        return False

    def signup_client(self):
        self.soc.send("SIGNUP".encode())
        mess_from_server = self.soc.recv(1024).decode()
        self.soc.send(input(mess_from_server).encode())
        mess_from_server = self.soc.recv(1024).decode()
        self.soc.send(input(mess_from_server).encode())

        mess_from_server = self.soc.recv(1024).decode()
        print(mess_from_server)
        if mess_from_server == "Signup successful.":
            return True
        return False

    def listen_server(self):
        while self.server_status:
            try:
                print("I'm waiting for you...")
                server_soc, address = self.soc_alive.accept()
                mess = server_soc.recv(1024).decode()
                print(mess)
                if "PING" in mess:
                    server_soc.send("300_alive".encode())
                elif "TAKE_FILE" in mess:
                    
                    server_soc.send("500_oke".encode())
                    self.send_file(server_soc)
            except socket.error as e:
                server_soc.send("301_dead".encode())
                print(f"Error: {e}")
                break

    def author (self, message):
        if message == "signin":
            if self.signin_client():
                thread = threading.Thread(target=client.listen_server)
                thread.daemon = False
                thread.start()
            else:
                print("login fail")
        else:
            if self.signup_client():
                thread = threading.Thread(target=client.listen_server)
                thread.daemon = False
                thread.start()
            else: 
                print("signup fail")
    
    def publish(self, lname, fname):
        self.soc.send("ASK -publish".encode())
        try:
            mess_from_server = self.soc.recv(1024).decode()
            if mess_from_server == "Give me the lname and fname":
                to_send = {"lname": lname, "fname": fname}
                to_send = json.dumps(to_send)
                self.soc.send(to_send.encode())
            elif mess_from_server == "You can't publish any file":
                print("oke khong publish nua")
        except:
            print("erroroororororo")
            
    def send_file(self, connection):
        print("in g f")
        lname = connection.recv(1024).decode()

        if os.path.exists(lname):
            connection.sendall("500_have".encode())

            file = open(lname, "rb")
            data = file.read()

            connection.sendall(str(len(data)).encode())

            connection.recv(1024).decode()

            for i in range(0, len(data), 1024):
                connection.sendall(data[i:i + 1024])
                connection.recv(1024).decode()

            file.close()
        else:
            connection.sendall("RESPONSE 404".encode())
    
    def take_file(self, ipaddr, port, lname):
        socket_send_take = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            print("in t f")
            socket_send_take.connect((ipaddr, port + 1))
            print("in t f")
            socket_send_take.sendall("TAKE_FILE".encode())
            print("in t f")
            rec = socket_send_take.recv(1024).decode()

            print("client", (ipaddr, port + 1), ", sends", rec)
            if rec == "500_oke":
                socket_send_take.sendall(lname.encode())

                rec = socket_send_take.recv(1024).decode()

                print("client", (ipaddr, port), ", sends", rec)

                size = socket_send_take.recv(1024).decode()

                socket_send_take.sendall("CHECK".encode())

                data = b""
                for _ in range(int(size) // 1024 + 1):
                    try:
                        rec = socket_send_take.recv(1024)
                        socket_send_take.sendall("CHECK".encode())
                        data += rec
                    except:
                        break

                directory = os.getcwd() + "/file_sharing"

                try:
                    os.mkdir(directory)
                except:
                    None

                file_name = directory + "/" + lname.split("/")[-1]
                file = open(file_name, "wb")

                file.write(data)
                file.close()
                print("fname: ", file_name)
                socket_send_take.close()

                return file_name

        except:
            return None
    def fetch (self, fname):
        self.soc.send("ASK -file".encode())
        try:
            mess_from_server = self.soc.recv(1024).decode()
            print(mess_from_server)
            if mess_from_server == "Give me the filename.":
                self.soc.send(fname.encode())
                list = self.soc.recv(1024).decode()
                list = json.loads(list)
                print(list)
                for l in list:
                    ipaddr, port = l["ipaddr"], l["port"]
                    lname = l["lname"]
                    print(ipaddr, port, lname)
                    if (ipaddr, port) == self.soc.getsockname():
                        print("File in your local: ", lname)
                        return None
                    else:
                        filename = self.take_file(ipaddr, port, lname)
                    if filename:
                        print(filename)
                        return filename
        except:
            print("ask file errror")
            return None

    def __del__(self):
        print("client off !!")
        self.server_status = False
        self.soc.close()

client = Client()
if client.server_status:
    client.author("signin")
    # client.publish("/home/yanzy/Downloads/Lab_1c_Packet Tracer_Simple  Network.pdf", "Lab_1c_Packet Tracer_Simple  Network.pdf")
    client.fetch("Lab_1c_Packet Tracer_Simple  Network.pdf")



