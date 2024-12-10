import socket
import select
import struct
import os
import random
from ip_protocol_numbers import IPProtocols
from icmp_types import ICMPTypes

ETHERNET_HEADER_SIZE = 14


class IcmpException(Exception):
    def __init__(self, message):
        super().__init__(message)


class IpException(Exception):
    def __init__(self, message):
        super().__init__(message)


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

    # sum &= 0xFFFFFFFF

    while sum >> 16:
        sum = (sum >> 16) + (sum & 0xFFFF)
    # sum += sum >> 16
    answer = ~sum & 0xFFFF
    return answer
    pass


def handle_udp_header(data: bytes, ip_header: dict):
    """
     0      7 8     15 16    23 24    31
    +--------+--------+--------+--------+
    |     Source      |   Destination   |
    |      Port       |      Port       |
    +--------+--------+--------+--------+
    |                 |                 |
    |     Length      |    Checksum     |
    +--------+--------+--------+--------+
    |
    |          data octets ...
    +---------------- ...
    """
    if len(data) < 8:
        raise ValueError(f"UDP header must be equal 8({len(data)=})")
    header = {}
    (
        header["source_port"],
        header["destination_port"],
        header["length"],
        header["checksum"],
    ) = struct.unpack("!HHHH", data[0:8])

    data_len = len(data)
    # if(data_len%2!=0):
    # data_len+=1
    pseudo_heder = (
        socket.inet_aton(ip_header["source_addr"])
        + socket.inet_aton(ip_header["destination_addr"])
        + struct.pack(
            "!BBH",
            0,
            17,
            data_len,
        )
    )

    # if len(pseudo_heder+data)%2==1:
    # check_sum = cksum(pseudo_heder+data+b'\x00')
    # else:
    # check_sum = cksum(pseudo_heder+data[:6]+b'\x00\x00'+data[8:])
    # print(check_sum, len(data), header["length"], header["checksum"])
    return data[8:], header


def handle_tcp_header(data: bytes):
    """
     0                   1                   2                   3
     0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |          Source Port          |       Destination Port        |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                        Sequence Number                        |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                    Acknowledgment Number                      |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |  Data |           |U|A|P|R|S|F|                               |
    | Offset| Reserved  |R|C|S|S|Y|I|            Window             |
    |       |           |G|K|H|T|N|N|                               |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |           Checksum            |         Urgent Pointer        |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                    Options                    |    Padding    |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                             data                              |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    """
    if len(data) < 20:
        raise ValueError(f"TCP header must be greater or equal 20({len(data)=})")
    header = {}
    (
        header["source_port"],
        header["destination_port"],
        header["sequence_number"],
        header["acknowlegment_number"],
        flags_and_offset,
        header["window"],
        header["checksum"],
        header["urgent_pointer"],
    ) = struct.unpack("!HHIIHHHH", data[0:20])
    header["data_offset"] = (flags_and_offset >> 12) & 0x0F
    header["NS"] = (flags_and_offset >> 8) & 0x01
    header["CWR"] = (flags_and_offset >> 7) & 0x01
    header["ECE"] = (flags_and_offset >> 6) & 0x01
    header["URG"] = (flags_and_offset >> 5) & 0x01
    header["ACK"] = (flags_and_offset >> 4) & 0x01
    header["PSH"] = (flags_and_offset >> 3) & 0x01
    header["RST"] = (flags_and_offset >> 2) & 0x01
    header["SYN"] = (flags_and_offset >> 1) & 0x01
    header["FIN"] = (flags_and_offset >> 0) & 0x01
    data_offset = header["data_offset"] * 4
    header["options"] = data[20:data_offset]
    if len(data) < data_offset:
        raise ValueError(
            f"Data size must be greater or equal {data_offset} ({len(data)=})"
        )

    return data[data_offset:], header


def handle_icmp_header(data):
    """
     0                   1                   2                   3
     0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |     Type      |      Code     |          Checksum             |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                        Data (optional)                        |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    """
    length = len(data)
    if length < 8:
        raise ValueError(
            f"ICMP header must be grater or equal 8 (len(data)={len(data)}) "
        )

    header = {}
    # icmp_type, code, checksum, identifier, sequence_number
    (
        header["type"],
        header["code"],
        header["checksum"],
        header["identifier"],
        header["sequence_number"],
    ) = struct.unpack("!BBHHH", data[0:8])

    if cksum(data) != 0:
        raise IcmpException("Wrong checksum in ICMP header.")

    return data, header
    pass


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
    if header["version"] != 4:
        raise IpException(f"Wrong IP version {header['version']}")
    header["source_addr"] = socket.inet_ntoa(data[12:16])
    header["destination_addr"] = socket.inet_ntoa(data[16:20])
    # print(version_and_IHL & 0xf)
    hsize = header["IHL"] * 4
    if hsize > 20:
        header["options"] = data[20:hsize]
    if header["total_length"] < len(data):
        raise IpException(f"wrong data length({header['total_length']=}!={len(data)=})")
    if cksum(data[:hsize]) != 0:
        raise IpException("Wrong checksum in IP header.")
    return data[hsize:], header


def ethernet(data: bytes):
    if len(data) < ETHERNET_HEADER_SIZE:
        raise Exception("Ethernet")
    return data[ETHERNET_HEADER_SIZE:]


def main():
    # with socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0800)) as sock:
    with socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x03)) as sock:
        # sock.bind(("eth0", 0))
        while True:
            rready, _, _ = select.select([sock], [], [])
            for conn in rready:
                data = conn.recv(2048)
                data = ethernet(data)
                try:
                    data, ip_header = handle_ip_header(data)

                    # unread_data_size = (
                    # ip_header["total_length"] - ip_header["IHL"] * 4 - len(data)
                    # )
                    # print(unread_data_size)
                    # unread_data = b""
                    # while unread_data_size - len(unread_data) > 0:
                    # unread_data += conn.recv(unread_data_size - len(unread_data))
                    # print(ip_header['total_length'],unread_data_size, len(unread_data))
                    # if(len(unread_data)!=unread_data_size):
                    # print(len(data))
                    # data += unread_data

                    packet_desc = ""
                    if ip_header["protocol"] == 17:
                        data, udp_header = handle_udp_header(data, ip_header)
                        packet_desc = (
                            f"{udp_header['source_port']:>6} -> {udp_header['destination_port']:<6}"
                            f"Len={udp_header['length']}"
                        )
                        # print(udp_header)
                    if ip_header["protocol"] == 6:
                        data, tcp_header = handle_tcp_header(data)
                        packet_desc = (
                            f"{tcp_header['source_port']:>6} -> {tcp_header['destination_port']:<6}"
                            f"Seq={tcp_header['sequence_number']} Ack={tcp_header['acknowlegment_number']} "
                            f"Win={tcp_header['window']} Len={len(data)} "
                        )

                    if ip_header["protocol"] == 1:
                        data, icmp_header = handle_icmp_header(data)
                        packet_desc = (
                            f"{ICMPTypes[icmp_header['type']]:<23} id={icmp_header['identifier']:#06x}, "
                            f"seq={icmp_header['sequence_number']}, ttl={ip_header['time_to_live']}"
                        )
                    #     print(len(data))

                    print(
                        f"{ip_header['source_addr']:>15} -> {ip_header['destination_addr']:<15} "
                        f"{IPProtocols[ip_header['protocol']]:<5}"
                        f"{ip_header['total_length']:>6}"
                        f" {packet_desc}"
                    )
                    # print(data)
                except IpException as e:
                    pass
                    # print(e)
    pass


if __name__ == "__main__":
    main()
