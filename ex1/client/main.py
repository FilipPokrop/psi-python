import select
import socket
import sys
import argparse
import os
import time
from errno import EINPROGRESS

PORT = os.getenv("PORT", default=42069)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", default="server", nargs="?")
    parser.add_argument("port", default=PORT, type=int, nargs="?")
    arguments = parser.parse_args()

    hostname = socket.gethostname()
    host_addr = socket.gethostbyname(hostname)

    server = arguments.destination
    port = arguments.port

    print(f"Destination: {server}")
    print(f"Port: {port}")
    print(f"Destination address: {socket.gethostbyname(server)}")

    print(f"Hostname: {hostname}")
    print(f"Address: {host_addr}")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setblocking(False)
        poll = select.poll()
        poll.register(sock, select.POLLOUT)
        try:
            sock.connect((server, port))
        except socket.error as e:
            if e.errno != EINPROGRESS:
                print(f"Error: {e}")
                exit(1)
            print("Connection in progress... waiting for server response.")

        for _, event in poll.poll(None):
            if event & select.POLLERR:
                try:
                    sock.send(b"")
                except OSError as e:
                    print(e)
                    exit(1)
        print("Connected to server successfully.")
        close = False
        while not close:
            rread, _, _ = select.select([sock, sys.stdin], [], [])
            for fd in rread:
                if fd is sock:
                    msg = sock.recv(2048)
                    if len(msg) == 0:
                        print(f"Server has closed connection")
                        close = True
                    print()

                elif fd is sys.stdin:
                    msg = sys.stdin.readline()
                    if msg == "":
                        close = True
                    sock.send(msg[:-1].encode())


    print("Exit")
