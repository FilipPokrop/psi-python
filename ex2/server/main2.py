import socket
import select
import time


class Server:
    def __init__(self, port):
        self.port = port
        self.sock = None
        self.rlist = []
        self.wlist = []
        self.xlist = []
        self.clients_data = {}
        self.init()
        pass

    def __del__(self):
        print("close socket")
        if self.sock is not None:
            self.sock.close()

    def init(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("0.0.0.0", self.port))
        sock.listen()
        self.rlist.append(sock)
        self.sock = sock
        print(f"Init socket on port {self.port}")

    def close_sockets(self):
        for conn in self.rlist:
            conn.close()
        for conn in self.wlist:
            conn.close()
        for conn in self.xlist:
            conn.close()

    def handle_read(self, conn: socket.socket):
        if conn.fileno() < 0:
            return
        if conn is self.sock:
            self.add_conn(conn)
        else:
            self.read_data(conn)

    def handle_except(self, conn: socket.socket):
        if conn.fileno() < 0:
            return
        data = conn.recv(1, socket.MSG_OOB)
        print(f"Recive OOB data: {data}")
        self.close_socket(conn)

    def read_data(self, conn: socket.socket):
        data = conn.recv(1024)
        if not data:
            self.close_socket(conn)
            return
        client_data = self.clients_data[conn]
        client_data["size"] += len(data)
        addr, _ = client_data["addr"]
        print(f'{addr}: total recive {client_data["size"]/1024} kb.')
        time.sleep(0.5)

    def close_socket(self, conn: socket.socket):
        if conn in self.rlist:
            self.rlist.remove(conn)
        if conn in self.wlist:
            self.wlist.remove(conn)
        if conn in self.xlist:
            self.xlist.remove(conn)

        if conn in self.clients_data:
            self.clients_data.pop(conn)

        conn.close()
        print("close connection")

    def add_conn(self, conn: socket.socket):
        new_conn, addr = conn.accept()
        self.clients_data[new_conn] = {"addr": addr, "size": 0}
        self.rlist.append(new_conn)
        self.xlist.append(new_conn)
        print(f"{addr[0]}: create connection")

    def run(self):
        while True:
            ready_to_read, _, ready_to_except = select.select(
                self.rlist, self.wlist, self.xlist
            )
            for conn in ready_to_except:
                self.handle_except(conn)
            for conn in ready_to_read:
                self.handle_read(conn)


if __name__ == "__main__":
    port = 42069

    hostname = socket.gethostname()
    host_arrd = socket.gethostbyname(hostname)

    print(f"hostname: {hostname}")
    print(f"addres: {host_arrd}")

    server = Server(port)
    server.run()
