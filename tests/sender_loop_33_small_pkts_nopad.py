#!/usr/bin/python3

import socket
import struct
import fcntl
import time
import threading
import argparse
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
    message = b"AbcdAbcdAbcdAbcdAbcdAbcdAbcdAbcd1"
    msg_len = len(message) // 4
    payload = struct.pack(f">{len(message)}s", message)
    return payload


def atomic_write(path, text):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        f.write(text)
    os.replace(tmp, path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kbps-start", type=int, default=250)
    parser.add_argument("--kbps-end", type=int, default=1000)
    parser.add_argument("--duration", type=float, default=60.0, help="duration per throughput in seconds")
    parser.add_argument("--interface", default="h1-eth0")
    parser.add_argument("--target-mac", default="00:00:00:00:00:02")
    parser.add_argument("--target-ip", default="10.0.1.2")
    parser.add_argument("--source-ip", default="10.0.1.1")
    parser.add_argument("--target-port", type=int, default=5001)
    parser.add_argument("--source-port", type=int, default=12345)
    parser.add_argument("--control-file", default="./tests_control.txt", help="path for control messages")
    parser.add_argument("--signal-file", default="./tests_signal.txt", help="path where monitor writes fullness signals")
    parser.add_argument("--monitor-log", default="../mininet/logs/s1.log", help="path to monitor log to tail for fullness")
    parser.add_argument("--debug", action="store_true", help="enable debug output from tailer")
    parser.add_argument("--output-file", default="./tests_output.txt", help="path for output result")
    args = parser.parse_args()

    payload = make_payload()
    target_mac_bytes = bytes.fromhex(args.target_mac.replace(':', ''))
    source_mac = get_interface_mac(args.interface)

    eth_sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0003))
    eth_sock.bind((args.interface, 0))

    total_pkt_size_bytes = 14 + 20 + 8 + 1 + 1 + len(payload) - (0) + 1  # approximate
    start_kbps = args.kbps_start

    time.sleep(2)

    # background tailer: watches args.monitor_log and sets queue_full_event when 'Queue is full' appears
    queue_full_event = threading.Event()
    stop_tailer = threading.Event()
    reset_tailer = threading.Event()

    def tail_log(path, fullness_event, stop_event, signal_file, reset_event):
        fp = None
        pos = 0
        while not stop_event.is_set():
            if args.debug:
                try:
                    print(f"[tailer] loop start, fp={'open' if fp else 'closed'}, pos={pos}")
                except Exception:
                    pass
            if reset_event.is_set():
                # on reset, position the reader to the current end of file
                try:
                    if fp:
                        fp.seek(0, os.SEEK_END)
                        pos = fp.tell()
                        if args.debug:
                            print(f"[tailer] reset -> seek to end pos={pos}")
                except Exception:
                    pass
                reset_event.clear()

            if fp is None:
                try:
                    fp = open(path, "r")
                    fp.seek(0, os.SEEK_END)
                    pos = fp.tell()
                    if args.debug:
                        print(f"[tailer] opened {path}, start pos={pos}")
                except Exception:
                    fp = None
                    time.sleep(0.5)
                    continue

            try:
                # check current file size
                fp.seek(0, os.SEEK_END)
                cur_end = fp.tell()
                if cur_end < pos:
                    # truncated/rotated: seek to end and skip old content
                    fp.seek(0, os.SEEK_END)
                    pos = fp.tell()
                    time.sleep(0.1)
                    continue

                if cur_end == pos:
                    # no new data
                    time.sleep(0.01)
                    continue

                # read newly appended lines incrementally to avoid large allocations
                fp.seek(pos)
                found = False
                while True:
                    line = fp.readline()
                    if not line:
                        break
                    if args.debug:
                        print(f"[tailer] read line: {line.rstrip()}")
                    if "queue is full" in line.lower():
                        found = True
                        if args.debug:
                            print("[tailer] matched 'queue is full' (case-insensitive)")
                        break
                pos = fp.tell()

                if found:
                    try:
                        tmp_inc = signal_file + ".tmp"
                        with open(tmp_inc, "w") as f:
                            f.write("increment\n")
                        os.replace(tmp_inc, signal_file)
                    except Exception:
                        pass
                    fullness_event.set()
                    # wait until main clears the event before continuing
                    while not stop_event.is_set() and fullness_event.is_set():
                        time.sleep(0.05)
                else:
                    # small sleep to avoid busy loop
                    time.sleep(0.01)
            except Exception:
                try:
                    fp.close()
                except Exception:
                    pass
                fp = None
                pos = 0
                time.sleep(0.5)

    tailer = threading.Thread(target=tail_log, args=(args.monitor_log, queue_full_event, stop_tailer, args.signal_file, reset_tailer), daemon=True)
    tailer.start()
    kept = False

    for max_msg_per_agg in range(3, 44, 4):
        if max_msg_per_agg == 7 and not kept:
            max_msg_per_agg -= 4
            kept = True
        for kbps in range(start_kbps, args.kbps_end, 50):
            time.sleep(4)  # wait a bit to clear the msg register arrays
            packet_sent_count = 0
            throughput_bps = kbps * 1000
            # compute pps and delay based on payload length
            pps = throughput_bps / (total_pkt_size_bytes * 8)
            delay = 1.0 / pps if pps > 0 else 1.0

            # announce new throughput via control file
            # reset tailer so it only reads log lines produced after this announce
            reset_tailer.set()
            atomic_write(args.control_file, f"throughput:{kbps}\ndelay:{delay}\npps:{pps}\n")
            print(f"ANNOUNCE throughput={kbps} kbps delay={delay:.6f}s pps={pps:.2f}")

            end_time = time.time() + args.duration
            detected_full = False
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

                # check if tailer signaled queue-full
                if queue_full_event.is_set():
                    # clear event for next round and break to next throughput
                    queue_full_event.clear()
                    print("SENDER detected queue-full via tailer")
                    detected_full = True
                    break

                # sleep for the remaining time in the delay interval if no break happened
                elapsed = time.time() - start
                sleep_time = max(0, delay - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)

            if detected_full:
                print(f"DETECTED 'Queue is full' in monitor log: stopping message sending at {kbps} kbps.")
                start_kbps = kbps - 50
                # write results to output file
                with open(args.output_file, "a") as f:
                    f.write(f"Max messages per agg. packet: {max_msg_per_agg}   -   Maximum throughput: {kbps - 50} kbps\n")
                break

    # signal stop
    atomic_write(args.control_file, "stop\n")
    print("ANNOUNCE stop")
    # stop tailer thread
    stop_tailer.set()
    try:
        tailer.join(timeout=1.0)
    except Exception:
        pass
    eth_sock.close()


if __name__ == "__main__":
    main()
