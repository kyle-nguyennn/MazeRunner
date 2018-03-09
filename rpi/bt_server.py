import bluetooth
import time


class BtServer():
    def __init__(self, channel, buffer_size=1024):
        self.lock = False
        self.channel = channel
        self.buffer_size = buffer_size
        self.server_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)

    def run(self):
        self.server_socket.bind(("", self.channel))
        self.server_socket.listen(1)
        port = self.server_socket.getsockname()[1]
        uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"

        bluetooth.advertise_service(self.server_socket, "MDPGrp7-BT-Server",
                                    service_id=uuid,
                                    service_classes=[
                                        uuid, bluetooth.SERIAL_PORT_CLASS],
                                    profiles=[bluetooth.SERIAL_PORT_PROFILE],
                                    # protocols = [ OBEX_UUID ]
                                    )
        print("BtServer - Waiting for connection on RFCOMM channel {}".format(port))

    def accept(self):
        self.client_conn, addr = self.server_socket.accept()
        self.connected = True
        print(
            "BtServer - Accepted connection from {}:{}".format(addr[0], addr[1]))

    def recv(self):
        try:
            data = self.client_conn.recv(self.buffer_size)
        except:
            return None
        if len(data) == 0:
            return None
        data_s = data.decode('utf-8')
        print("BtServer - Received data: {}".format(data_s), end='')
        return data_s

    def send(self, data):
        try:
            self.client_conn.send((data+"\r\n").encode('utf-8'))
            print("BtServer - Sent data: {}".format(data))
        except:
            print("BtServer - Error sending data: {}".format(data))

    def close_client(self):
        try:
            self.client_conn.close()
            self.connected = False
            print("BtServer - Client disconnected")
        except:
            pass

    def close_server(self):
        try:
            self.server_socket.close()
            print("BtServer - Server closed")
        except:
            pass
