import socket
import select
import struct
import argparse
import time
import itertools
import os
from stats import Statistics


class IcmpException(Exception):
    def __init__(self, message):
        super().__init__(message)


class IpException(Exception):
    def __init__(self, message):
        super().__init__(message)


HEADER_SIZE = 8
PID = os.getpid()

stats = Statistics()


def cksum(source: bytes):
    # nleft = len(source)
    sum = 0
    for i in range(0, len(source) // 2 * 2, 2):
        l_byte = source[i + 1]
        h_byte = source[i + 0]

        sum += (h_byte << 8) + l_byte
    if len(source) % 2 == 1:
        l_byte = source[-1] << 8
        sum += l_byte

    sum &= 0xFFFFFFFF

    sum = (sum >> 16) + (sum & 0xFFFF)
    sum += sum >> 16
    answer = ~sum & 0xFFFF
    return answer
    pass


def send_ping(sock: socket.socket, addr, data_len: int, seq_num: int):
    data = b"Q" * (data_len - 8)
    header = struct.pack("!BBHHH", 8, 0, 0, PID & 0xFFFF, seq_num)
    check_sum = cksum(header + data)
    header = struct.pack("!BBHHH", 8, 0, check_sum, PID & 0xFFFF, seq_num)
    packet = header + data
    sock.sendto(packet, addr)


def recive_ping(
    sock: socket.socket, addr, data_len: int, seq_num: int, t_start: int, timeout: float
):
    while timeout > 0:
        rread, _, _ = select.select([sock], [], [], timeout)
        t_stop = time.time_ns()
        if len(rread) == 0:
            return None

        for conn in rread:
            if conn is sock:
                data, addr = sock.recvfrom(2048)
                try:
                    data, ip_header = handle_ip_header(data)
                    data, icmp_header = handle_icmp_header(data)
                    if icmp_header["code"] != 0:
                        continue
                        print(data)
                        pass
                    if icmp_header["sequence_number"] != seq_num:
                        continue
                    triptime = (t_stop - t_start) / 1000000
                    print(
                        f"{len(data)} bytes from {ip_header['source_addr']}:",
                        f"icmp_seq={icmp_header['sequence_number']}",
                        f"ttl={ip_header['time_to_live']}",
                        f"time {triptime}ms",
                    )

                    return t_stop
                except IcmpException as e:
                    print(e)
                timeout -= (t_stop - t_start) / 1_000_000_000

    pass
    return None


def ping(sock: socket.socket, addr, data_len: int, seq_num: int, timeout: float):
    send_ping(sock, addr, data_len, seq_num)
    t_start = time.time_ns()
    stats.send()

    t_stop = recive_ping(sock, addr, data_len, seq_num, t_start, timeout)
    if t_stop is None:
        return timeout
    triptime = (t_stop - t_start) / 1000000
    stats.recive(triptime)
    return triptime / 1000


def handle_ip_header(data: bytes):
    """
     0                   1                   2                   3
     0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |Version|  IHL  |Type of Service|          Total Length         |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |         Identification        |Flags|      Fragment Offset    |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |  Time to Live |    Protocol   |         Header Checksum       |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                       Source Address                          |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                    Destination Address                        |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                    Options                    |    Padding    |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    """
    # należy dodac sprawdzanie czy nagłówek jest poprawny
    if len(data) < 20:
        raise ValueError(
            f"IP header must be grater or equal 20 (len(data)={len(data)}) "
        )
    header = {}
    (
        version_and_IHL,
        header["TOS"],
        header["total_length"],
        header["identification"],
        flags_and_fragment_offset,
        header["time_to_live"],
        header["protocol"],
        header["header_checksum"],
    ) = struct.unpack("!BBHHHBBH", data[0:12])
    header["IHL"] = version_and_IHL & 0xF
    header["version"] = version_and_IHL >> 4 & 0xF
    header["source_addr"] = socket.inet_ntoa(data[12:16])
    header["destination_addr"] = socket.inet_ntoa(data[16:20])
    if header["version"] != 4:
        raise IpException("Wrong IP version")
    # print(version_and_IHL & 0xf)
    hsize = header["IHL"] * 4
    if hsize > 20:
        header["options"] = data[20:hsize]
    if cksum(data[:hsize]) != 0:
        raise IpException("Wrong checksum in IP header.")
    return data[hsize:], header


def handle_icmp_header(data: bytes):
    """
     0                   1                   2                   3
     0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |     Type      |     Code      |          Checksum             |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |           Identifier          |        Sequence Number        |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |     Data ...
    +-+-+-+-+-
    """
    length = len(data)
    if length < 8:
        raise ValueError(
            f"ICMP header must be grater or equal 8 (len(data)={len(data)}) "
        )

    icmp_type, code, checksum, identifier, sequence_number = struct.unpack(
        "!BBHHH", data[0:8]
    )

    if icmp_type != 0:
        raise IcmpException(f"Wrong type in ICMP header expected 0 recived {icmp_type}")

    # if code != 0:
    #     raise IcmpException(
    #         f'Wrong code in ICMP header expected 0 recived {code}')

    # calc_checksum = cksum(data[:2]+b'\x00\x00'+data[4:])
    if cksum(data) != 0:
        raise IcmpException("Wrong checksum in ICMP header.")

    header = {
        "type": icmp_type,
        "code": code,
        "checksum": checksum,
        "identifier": identifier,
        "sequence_number": sequence_number,
    }

    return data, header

    pass


def main():
    # print(PID)

    parser = argparse.ArgumentParser()
    parser.add_argument("destination")
    parser.add_argument("-c", "--count", dest="count", type=int, help="stop after COUNT replies")
    parser.add_argument(
        "-s", "--size",
        dest="size",
        type=int,
        default=64,
        help="use SIZE as number of data bytes to be sent",
    )
    parser.add_argument(
        "-w", "--wait", dest="wait", type=float, default=1.0, help="time to wait for response"
    )
    args = parser.parse_args()

    destination = args.destination
    if (count := args.count) is not None:
        count = int(count)
    addr = None
    try:
        addr_list = socket.getaddrinfo(destination, None)
        # print(len(addr_list))
        for af, sock, _, _, a in addr_list:
            if af == socket.AF_INET:
                addr = a
                print(addr)
                break
    except socket.gaierror as e:
        print(f"ping: {destination}: {e}")
        exit(1)

    with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP) as sock:
        try:
            for i in itertools.count():
                if i == count:
                    break
                triptime = ping(sock, addr, int(args.size), i, float(args.wait))
                time.sleep(max(0, 1 - triptime))
        except KeyboardInterrupt:
            pass
            print()
        finally:
            print(f"--- {destination} ping statistics ---")
            print(stats)

    pass


if __name__ == "__main__":
    main()
