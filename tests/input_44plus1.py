#!/usr/bin/python3

import socket
import struct
import fcntl
import os

def checksum(data):
    if len(data) % 2 == 1:
        data += b"\x00"
    total = 0
    for index in range(0, len(data), 2):
        total += (data[index] << 8) + data[index + 1]
    total = (total >> 16) + (total & 0xFFFF)
    total += total >> 16
    return (~total) & 0xFFFF


def get_interface_mac(iface_name):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        ifreq = struct.pack("256s", iface_name.encode("utf-8")[:15])
        response = fcntl.ioctl(sock.fileno(), 0x8927, ifreq)
        return response[18:24]
    finally:
        sock.close()


def build_udp_frame(dst_mac, src_mac, src_ip_addr, dst_ip_addr, src_port, dst_port, payload):
    udp_length = 8 + len(payload)
    udp_header = struct.pack("!HHHH", src_port, dst_port, udp_length, 0)
    pseudo_header = (
        socket.inet_aton(src_ip_addr)
        + socket.inet_aton(dst_ip_addr)
        + struct.pack("!BBH", 0, socket.IPPROTO_UDP, udp_length)
    )
    udp_checksum = checksum(pseudo_header + udp_header + payload)
    if udp_checksum == 0:
        udp_checksum = 0xFFFF
    udp_header = struct.pack("!HHHH", src_port, dst_port, udp_length, udp_checksum)

    total_length = 20 + udp_length
    ip_header = struct.pack(
        "!BBHHHBBH4s4s",
        0x45,
        0,
        total_length,
        0,
        0,
        64,
        socket.IPPROTO_UDP,
        0,
        socket.inet_aton(src_ip_addr),
        socket.inet_aton(dst_ip_addr),
    )
    ip_checksum = checksum(ip_header)
    ip_header = struct.pack(
        "!BBHHHBBH4s4s",
        0x45,
        0,
        total_length,
        0,
        0,
        64,
        socket.IPPROTO_UDP,
        ip_checksum,
        socket.inet_aton(src_ip_addr),
        socket.inet_aton(dst_ip_addr),
    )

    ethernet_header = struct.pack("!6s6sH", dst_mac, src_mac, 0x0800)
    return ethernet_header + ip_header + udp_header + payload


def make_payload():
    # build UDP payload similar to original test
    message = b"AbcdAbcdAbcdAbcdAbcdAbcdAbcdAbcdAbcdAbcdAbcd"
    msg_len = len(message) // 4

    # compute padding/plen as in original
    padding = b"\x00" * 15
    padding_len = 64 - 14 - 20 - 8 - 1 - 1 - 1 - int(msg_len) * 4
    plen = max(padding_len, 0)
    plen = min(plen, 15)

    if plen > 0:
        payload = struct.pack(f">BB{int(plen)}sB{len(message)}s", 0, plen, padding[:plen], msg_len, message)
    else:
        payload = struct.pack(f">BBB{len(message)}s", 0, plen, msg_len, message)

    return payload, plen, msg_len


def send_packet_once(target_mac, interface_name, source_ip, target_ip, source_port=12345, target_port=5001, payload=None):
    if payload is None:
        payload, plen, msg_len = make_payload()
    else:
        # best-effort to compute meta from payload length
        plen = None
        msg_len = None

    target_mac_bytes = bytes.fromhex(target_mac.replace(":", ""))
    source_mac = get_interface_mac(interface_name)
    frame = build_udp_frame(
        target_mac_bytes,
        source_mac,
        source_ip,
        target_ip,
        source_port,
        target_port,
        payload,
    )
    eth_sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0003))
    eth_sock.bind((interface_name, 0))
    eth_sock.send(frame)
    eth_sock.close()
    return payload, plen, msg_len


if __name__ == "__main__":
    # simple CLI behavior: send one packet with defaults
    TARGET_MAC = "00:00:00:00:00:02"
    TARGET_IP = "10.0.1.2"
    INTERFACE = "h1-eth0"
    SOURCE_IP = "10.0.1.1"

    payload, plen, msg_len = send_packet_once(TARGET_MAC, INTERFACE, SOURCE_IP, TARGET_IP)
    print(f"Sent one packet to {TARGET_MAC} ({TARGET_IP}) payload={payload.hex()}")
