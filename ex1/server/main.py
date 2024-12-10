import socket
import select
import time
import threading


BUFFER_SIZE = 1024


def handle_connection(conn, addr, end: threading.Event):
    addr, port = addr

    exit_loop = False
    try:
        print(f"New connection from: {addr}")

        while exit_loop:
            ready_to_read, _, _ = select.select([conn], [], [], 1.)
            if end.isSet():
                exit_loop = True 
                break
            for sock in ready_to_read:
                data = conn.recv(BUFFER_SIZE).decode()
                if not data:
                   exit_loop = True 

                print(f"{addr}: {data}")
    finally:
        print(f"Closing connection from: {addr}")
        conn.close()


if __name__ == "__main__":
    rlist = []
    wlist = []
    xlist = []

    threads = []

    addresses = {}

    port = 42069

    hostname = socket.gethostname()
    host_addr = socket.gethostbyname(hostname)

    print(f"Hostname: {hostname}")
    print(f"Address: {host_addr}")

    end_event = threading.Event()

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            # set socket non blocking
            sock.setblocking(False)

            # add socket to reader list
            rlist.append(sock)

            sock.bind(("0.0.0.0", port))
            sock.listen()
            print(f"Listening on port: {port}")

            while True:
                ready_to_read, _, _ = select.select(rlist, wlist, xlist)
                for conn in ready_to_read:
                    if conn is sock:
                        new_conn, addr = conn.accept()
                        thread = threading.Thread(
                            target=handle_connection, args=(new_conn, addr, end_event)
                        )
                        # thread.daemon = True
                        thread.start()
                        threads.append(thread)
    except KeyboardInterrupt as e:
        end_event.set()
        print("Server is shut down")
