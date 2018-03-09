import socket
import time


class TcpServer():
    def __init__(self, ip, port, buffer_size=1024):
        self.lock = False
        self.ip = ip
        self.port = port
        self.buffer_size = buffer_size
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def run(self):
        self.server_socket.bind((self.ip, self.port))
        self.server_socket.listen(1)
        print("TcpServer - Listening on {}:{}".format(self.ip, self.port))

    def accept(self):
        self.client_conn, addr = self.server_socket.accept()
        self.connected = True
        print(
            "TcpServer - Accepted connection from {}:{}".format(addr[0], addr[1]))

    def recv(self):
        try:
            data = self.client_conn.recv(self.buffer_size)
        except:
            return None
        if not data:
            return None
        data_s = data.decode('utf-8')
        print("TcpServer - Received data: {}".format(data_s), end='')
        return data_s

    def send(self, data):
        try:
            self.client_conn.send((data+"\n").encode('utf-8'))
            print("TcpServer - Sent data: {}".format(data))
        except:
            print("TcpServer - Error sending data: {}".format(data))

    def close_client(self):
        try:
            self.client_conn.close()
            self.connected = False
            print("TcpServer - Client disconnected")
        except:
            pass

    def close_server(self):
        try:
            self.server_socket.close()
            print("TcpServer - Server closed")
        except:
            pass
