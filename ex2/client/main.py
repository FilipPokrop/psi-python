import socket
import time
import argparse


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("destination", default="server", nargs="?")
    argparser.add_argument("-w", "--wait", default=0.4, type=float)
    argparser.add_argument("-s", "--size", default=4096, type=int)
    args = argparser.parse_args()

    hostname = socket.gethostname()
    host_addr = socket.gethostbyname(hostname)

    server = args.destination
    port = 42069
    wait_time = float(args.wait)
    package_size = int(args.size)

    print(f"Hostname: {hostname}")
    print(f"Address: {host_addr}")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            # connect to the server
            sock.connect((server, port))
            print("Connect")
            try:
                data_size = 0
                data = b"a" * package_size
                while True:
                    # send data every 400 ms
                    sock.send(data)
                    data_size += len(data)
                    print(f"Total data sent: {data_size/1024}kb")
                    time.sleep(wait_time)
            except KeyboardInterrupt:
                # send OOB data upon recive SIGINT
                print("OOB data sending")
                data = b"\x00"
                sock.send(data, socket.MSG_OOB)
                print(f"Total data sent: {data_size/1024}kb")

                pass
        except socket.error as e:
            print(f"Error: {e}")

    print("Exit")
