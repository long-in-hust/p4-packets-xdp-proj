#!/usr/bin/python3

import argparse
import fcntl
import socket
import struct


def checksum(data):
    if len(data) % 2 == 1:
        data += b"\x00"
    total = 0
    for index in range(0, len(data), 2):
        total += (data[index] << 8) + data[index + 1]
    total = (total >> 16) + (total & 0xFFFF)
    total += total >> 16
    return (~total) & 0xFFFF


def get_interface_mac(interface_name):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        ifreq = struct.pack("256s", interface_name.encode("utf-8")[:15])
        response = fcntl.ioctl(sock.fileno(), 0x8927, ifreq)
        return response[18:24]
    finally:
        sock.close()


def build_udp_frame(dst_mac, src_mac, src_ip, dst_ip, src_port, dst_port, payload):
    udp_length = 8 + len(payload)
    udp_header = struct.pack("!HHHH", src_port, dst_port, udp_length, 0)
    pseudo_header = (
        socket.inet_aton(src_ip)
        + socket.inet_aton(dst_ip)
        + struct.pack("!BBH", 0, socket.IPPROTO_UDP, udp_length)
    )
    udp_checksum = checksum(pseudo_header + udp_header + payload) or 0xFFFF
    udp_header = struct.pack(
        "!HHHH", src_port, dst_port, udp_length, udp_checksum
    )

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
        socket.inet_aton(src_ip),
        socket.inet_aton(dst_ip),
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
        socket.inet_aton(src_ip),
        socket.inet_aton(dst_ip),
    )

    ethernet_header = struct.pack("!6s6sH", dst_mac, src_mac, 0x0800)
    return ethernet_header + ip_header + udp_header + payload


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--interface", default="h1-eth0")
    parser.add_argument("--target-mac", default="00:00:00:00:00:02")
    parser.add_argument("--target-ip", default="10.0.1.2")
    parser.add_argument("--source-ip", default="10.0.1.1")
    parser.add_argument("--target-port", type=int, default=5001)
    parser.add_argument("--source-port", type=int, default=12345)
    args = parser.parse_args()

    payload = b"AbcdAbcdAbcdAbcdAbcdAbcdAbcdAbcd12"
    target_mac = bytes.fromhex(args.target_mac.replace(":", ""))
    source_mac = get_interface_mac(args.interface)
    frame = build_udp_frame(
        target_mac,
        source_mac,
        args.source_ip,
        args.target_ip,
        args.source_port,
        args.target_port,
        payload,
    )

    eth_sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0003))
    try:
        eth_sock.bind((args.interface, 0))
        for _ in range(128):
            eth_sock.send(frame)
    finally:
        eth_sock.close()


if __name__ == "__main__":
    main()
