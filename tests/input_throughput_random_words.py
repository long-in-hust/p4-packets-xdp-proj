#!/usr/bin/python3

import random
import subprocess
import ctypes
import fcntl
import socket
import struct
import time
import re

target_mac = "00:00:00:00:00:02"
target_ip = "10.0.1.2"
target_port = 5001
interface_name = "h1-eth0"
source_ip = "10.0.1.1"

# a list of messages of varying lengths to test different payload sizes
# ranging from 8 bytes to 36 bytes
msg_list = [
    b"AbcdAbcd", # 8 bytes
    b"AbcdAbcdAbcd", # 12 bytes
    b"AbcdAbcdAbcdAbcd", # 16 bytes
    b"AbcdAbcdAbcdAbcdAbcd", # 20 bytes
    b"AbcdAbcdAbcdAbcdAbcdAbcd", # 24 bytes
    b"AbcdAbcdAbcdAbcdAbcdAbcdAbcd", # 28 bytes
    b"AbcdAbcdAbcdAbcdAbcdAbcdAbcdAbcd", # 32 bytes
    b"AbcdAbcdAbcdAbcdAbcdAbcdAbcdAbcdAbcd", # 36 bytes
]

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

def read_queue_fullness():
    cmd = "echo 'register_read sw_ingress_control.queue_is_full 0' | psa_switch_CLI --thrift-ip localhost --thrift-port 9091"
    try:
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, text=True)
    except subprocess.CalledProcessError:
        return None
    m = int(out.strip()[-1])
    if m:
        return m
    return None

class udp_data(ctypes.Structure):
    _fields_ = [
        ("pkt_type", ctypes.c_uint8),
        ("plen", ctypes.c_uint8),
        ("padding", ctypes.c_char * 15),
        ("msg_len", ctypes.c_uint8),
        ("message", ctypes.c_char * 32)
    ]

udp_msg = udp_data()
udp_msg.pkt_type = 0
udp_msg.padding = b"\x00" * 15

target_mac_bytes = bytes.fromhex(target_mac.replace(":", ""))
source_mac = get_interface_mac(interface_name)
ethernet_sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0003))
ethernet_sock.bind((interface_name, 0))

for mbps in range(1, 31):
    print(f"Starting run at {mbps} Mbps (delay {delay:.6f}s) for 60 seconds")
    end_time = time.time() + 60
    consecutive_full = 0
    
    while time.time() < end_time:
        msg_index = random.randint(0, len(msg_list) - 1)
        udp_msg.message = msg_list[msg_index]
        udp_msg.msg_len = len(udp_msg.message) // 4

        padding_len = 64 - 14 - 20 - 8 - 1 - 1 - 1 - int(udp_msg.msg_len) * 4
        udp_msg.plen = max(padding_len, 0)
        udp_msg.plen = min(udp_msg.plen, 15)

        if udp_msg.plen > 0:
            payload = struct.pack(f">BB{udp_msg.plen}sB44s", udp_msg.pkt_type, udp_msg.plen, udp_msg.padding[:udp_msg.plen], udp_msg.msg_len, udp_msg.message)
        else:
            payload = struct.pack(">BBB44s", udp_msg.pkt_type, udp_msg.plen, udp_msg.msg_len, udp_msg.message)
        
        frame = build_udp_frame(
            target_mac_bytes,
            source_mac,
            source_ip,
            target_ip,
            12345,
            target_port,
            payload,
        )
        ethernet_sock.send(frame)
        print(
            f"Sent UDP frame to {target_mac} ({target_ip}:{target_port}) with payload: {payload.hex()}"
        )
        # check fullness after each packet
        fullness = read_queue_fullness()
        if fullness is not None:
            if fullness == 1:
                consecutive_full += 1
            else:
                consecutive_full = 0
        else:
            consecutive_full = 0

        if consecutive_full >= 2:
            print(f"Queue reported full twice consecutively at {mbps} Mbps.")
            break

        throughput_bps = mbps * 1_000_000
        total_pkt_size_bytes = 14 + 20 + 8 + 1 + 1 + udp_msg.plen + 1 + udp_msg.msg_len * 4
        pps = throughput_bps / (total_pkt_size_bytes * 8)
        delay = 1.0 / pps if pps > 0 else 1.0

        time.sleep(delay)

    if consecutive_full >= 2:
        print(f"Stopping throughput sweep at {mbps} Mbps due to consecutive full queue reports.")
        print(f"The maximum sustainable throughput is approximately {mbps - 1} Mbps.")
        break

print("Completed throughput sweep 1-30 Mbps")
ethernet_sock.close()