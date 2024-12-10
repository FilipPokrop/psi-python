import socket
import select
import time
import fcntl
import signal
import os
import argparse
import threading


def handle_sigurg(signum, frame):
    # close conection if recived OOB data
    global oob_msg
    oob_msg = True


def handle_connection(conn: socket.socket, addr: tuple, end_event: threading.Event):
    data_size = 0
    addr, port = addr

    while not end_event.is_set():
        # recive data from client and wait 500 ms
        data = conn.recv(buffer_size).decode()

        if not data:
            break

        # client_data = clients_data[conn]
        data_size += len(data)
        print(f"{addr}: Total recive: {data_size/1024} kb.")
        time.sleep(wait_time)

    print(f"Connection closed with {addr}")
    conn.close()


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("-w", "--wait", default=0.4, type=float)
    argparser.add_argument("-s", "--size", default=512, type=int)
    args = argparser.parse_args()

    buffer_size = int(args.size)
    wait_time = float(args.wait)

    rlist = []
    wlist = []
    xlist = []

    connections = dict()

    # set action for SIGURG signal
    oob_msg = False
    signal.signal(signal.SIGURG, handle_sigurg)

    clients_data = {}

    port = 42069

    hostname = socket.gethostname()
    host_arrd = socket.gethostbyname(hostname)

    print(f"Hostname: {hostname}")
    print(f"Address: {host_arrd}")

    # open socket and start listen
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setblocking(False)
            rlist.append(sock)
            # xlist.append(sock)

            sock.bind(("0.0.0.0", port))
            sock.listen()
            print(f"Server listening on port: {port}")

            while True:
                ready_to_read, _, exception_to_read = select.select(rlist, wlist, xlist)
                if oob_msg:
                    for conn in exception_to_read:
                        data = conn.recv(1, socket.MSG_OOB)
                        _, event = connections[conn]
                        event.set()
                        print(f"OOB data recived: {data}")
                        xlist.remove(conn)
                    oob_msg = False
                for conn in ready_to_read:
                    if conn is sock:
                        # create a connection with a new client
                        new_conn, addr = conn.accept()
                        fcntl.fcntl(new_conn, fcntl.F_SETOWN, os.getpid())
                        end_event = threading.Event()
                        thread = threading.Thread(
                            target=handle_connection, args=(new_conn, addr, end_event)
                        )
                        # thread.daemon = True
                        connections[new_conn] = (thread, end_event)
                        thread.start()
                        xlist.append(new_conn)

                # Removing closed connections from the list.
                to_delete = [
                    key
                    for key, (thread, event) in connections.items()
                    if not thread.is_alive()
                ]
                for key in to_delete:
                    connections.pop(key)
    finally:
        for _, event in connections.values():
            event.set()
