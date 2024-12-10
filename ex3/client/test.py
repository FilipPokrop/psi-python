def ip_cksum(source: bytes):
    sum = 0
    for i in range(0, len(source) // 2 * 2, 2):
        l_byte = source[i + 1]
        h_byte = source[i + 0]

        sum += (h_byte << 8) + l_byte
    if len(source) % 2 == 1:
        l_byte = source[-1] << 8
        sum += l_byte

    sum &= 0xFFFFFFFF

    while (sum >> 16) != 0:
        sum = (sum >> 16) + (sum & 0xFFFF)
    answer = ~sum & 0xFFFF
    return answer


def test_ip_checksum():
    header = (
        b"\x45\x00\x00\x54\x54\xe8\x40\x00\x40\x01\x13\x9f\xc0\xa8"
        + b"\x01\x6a\x08\x08\x08\x08"
    )
    print(header)
    data = header[:10] + b"\x00\x00" + header[12:]
    print(ip_cksum(data))
    print((header[10] << 8) + header[11])


test_ip_checksum()
