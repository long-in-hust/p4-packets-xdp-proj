#!/usr/bin/python3

import socket
import struct
import fcntl
import time
import argparse
import os

worker_packets_count_list = [1, 2, 5, 10, 20, 40, 80, 160, 320, 640, 1023]

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
    message = b"AbcdAbcd"
    msg_len = len(message) // 4
    padding = b"\x00" * 15
    padding_len = 64 - 14 - 20 - 8 - 1 - 1 - 1 - int(msg_len) * 4
    plen = max(padding_len, 0)
    plen = min(plen, 15)
    if plen > 0:
        payload = struct.pack(f">BB{int(plen)}sB{len(message)}s", 0, plen, padding[:plen], msg_len, message)
    else:
        payload = struct.pack(f">BBB{len(message)}s", 0, plen, msg_len, message)
    return payload


def atomic_write(path, text):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        f.write(text)
    os.replace(tmp, path)


def read_and_clear_signal(path):
    try:
        with open(path, "r") as f:
            txt = f.read().strip()
    except Exception:
        return None
    try:
        os.remove(path)
    except Exception:
        pass
    return txt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kbps-start", type=int, default=30)
    parser.add_argument("--kbps-end", type=int, default=40)
    parser.add_argument("--duration", type=float, default=180.0, help="duration per throughput in seconds")
    parser.add_argument("--interface", default="h1-eth0")
    parser.add_argument("--target-mac", default="00:00:00:00:00:02")
    parser.add_argument("--target-ip", default="10.0.1.2")
    parser.add_argument("--source-ip", default="10.0.1.1")
    parser.add_argument("--target-port", type=int, default=5001)
    parser.add_argument("--source-port", type=int, default=12345)
    parser.add_argument("--control-file", default="./tests_control.txt", help="path for control messages")
    parser.add_argument("--signal-file", default="./tests_signal.txt", help="path where monitor writes fullness signals")
    parser.add_argument("--output-file", default="./tests_output.txt", help="path for output result")
    args = parser.parse_args()

    payload = make_payload()
    target_mac_bytes = bytes.fromhex(args.target_mac.replace(':', ''))
    source_mac = get_interface_mac(args.interface)

    eth_sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0003))
    eth_sock.bind((args.interface, 0))

    total_pkt_size_bytes = 14 + 20 + 8 + 1 + 1 + len(payload) - (0) + 1  # approximate
    start_kbps = args.kbps_start
    for worker_packet_limit in worker_packets_count_list:
        if worker_packet_limit > 5 and worker_packet_limit <= 10:
            start_kbps -= 1
        if worker_packet_limit > 10 and worker_packet_limit <= 20:
            start_kbps -= 2
        if worker_packet_limit > 20 and worker_packet_limit <= 30:
            start_kbps -= 3
        if worker_packet_limit > 30:
            start_kbps -= 3

        for kbps in range(start_kbps, args.kbps_end, 1):
            time.sleep(2)  # wait a bit to clear the msg register arrays
            packet_sent_count = 0
            throughput_bps = kbps * 1000
            # compute pps and delay based on payload length
            pps = throughput_bps / (total_pkt_size_bytes * 8)
            delay = 1.0 / pps if pps > 0 else 1.0

            # announce new throughput via control file
            atomic_write(args.control_file, f"throughput:{kbps}\ndelay:{delay}\npps:{pps}\n")
            print(f"ANNOUNCE throughput={kbps} kbps delay={delay:.6f}s pps={pps:.2f}")

            end_time = time.time() + args.duration
            while time.time() < end_time:
                start = time.time()
                frame = build_udp_frame(
                    target_mac_bytes,
                    source_mac,
                    args.source_ip,
                    args.target_ip,
                    args.source_port,
                    args.target_port,
                    payload,
                )
                eth_sock.send(frame)
                packet_sent_count += 1
                print(f"SENT {len(frame)} bytes to {args.target_mac} {args.target_ip}:{args.target_port}")
                print(f"Total packets sent for this throughput: {packet_sent_count}")

                # check signal from monitor: if 'full' then clear and move to next throughput
                sig = read_and_clear_signal(args.signal_file)
                if sig and sig.lower().startswith("full"):
                    break

                # sleep for the remaining time in the delay interval if no break happened
                elapsed = time.time() - start
                sleep_time = max(0, delay - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)

            if sig and sig.lower().startswith("full"):
                print(f"RECEIVED signal '{sig}' from monitor: stopping message sending at {kbps} kbps.")
                start_kbps = kbps
                # write results to output file
                with open(args.output_file, "a") as f:
                    f.write(f"Max number of msgs in agg packet: {worker_packet_limit}   -   Maximum throughput: {kbps} kbps\n")
                break

            if sig and sig.lower().startswith("finished"):
                print(f"RECEIVED signal '{sig}' from monitor: stopping all message sending.")
                break

    # signal stop
    atomic_write(args.control_file, "stop\n")
    print("ANNOUNCE stop")
    eth_sock.close()


if __name__ == "__main__":
    main()
