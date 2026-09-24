#!/usr/bin/python3

import time
import subprocess
import argparse
import os


def read_queue_fullness():
    cmd = "echo 'register_read sw_ingress_control.queue_is_full 0' | psa_switch_CLI --thrift-ip localhost --thrift-port 9091"
    try:
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, text=True)
    except subprocess.CalledProcessError:
        return None
    # try to parse a numeric value after '=' if present, otherwise fallback to last digit on the 4th line
    for line in out.splitlines():
        if "=" in line:
            right = line.split("=")[-1].strip()
            if right and right[0].isdigit():
                return int(right[0])
    lines = out.splitlines()
    if len(lines) >= 4 and lines[3]:
        ch = ''.join([c for c in lines[3] if c.isdigit()])
        if ch:
            return int(ch[-1])
    return None


def parse_control(path):
    try:
        with open(path, "r") as f:
            text = f.read()
    except Exception:
        return None
    if not text:
        return None
    if text.strip().lower().startswith("stop"):
        return {"cmd": "stop"}
    out = {}
    for line in text.splitlines():
        if not line:
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    if out:
        out["cmd"] = "throughput"
        return out
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--control-file", default="./tests_control.txt", help="path for control messages")
    parser.add_argument("--duration", type=float, default=18000.0, help="maximum total run duration in seconds")
    parser.add_argument("--signal-file", default="./tests_signal.txt", help="path where monitor writes fullness signals")
    args = parser.parse_args()

    max_num_packets_per_aggregation = 3
    cmd_set_max_num_packets_per_aggregation = f"echo 'register_write sw_ingress_control.max_num_packets_per_aggregation 0 {max_num_packets_per_aggregation}' | psa_switch_CLI --thrift-ip localhost --thrift-port 9091"

    cmd_reset_pipeline = "bash -c 'cd ..; python3 ctrl_plane/p4runtime_api/agg_switch.py --p4info build/l4_aggregate.p4info.txtpb --bmv2-json build/l4_aggregate.json'"

    os.system(cmd_set_max_num_packets_per_aggregation)

    end_time = time.time() + args.duration
    last_throughput = None
    consecutive_full = 0
    while time.time() < end_time:
        start = time.time()
        ctrl = parse_control(args.control_file)
        if ctrl is None:
            # no instruction yet; wait a bit
            time.sleep(0.01)
            continue
        if ctrl.get("cmd") == "stop":
            print("MONITOR received stop, exiting")
            break

        # follow sender's announced throughput and delay
        mbps = int(float(ctrl.get("throughput", 0)))
        delay = float(ctrl.get("delay", 0.1))
        pps = float(ctrl.get("pps", 0))
        if last_throughput != mbps:
            out = os.system(cmd_reset_pipeline)
            cmd_set_max_num_packets_per_aggregation = f"echo 'register_write sw_ingress_control.max_num_packets_per_aggregation 0 {max_num_packets_per_aggregation}' | psa_switch_CLI --thrift-ip localhost --thrift-port 9091"
            os.system(cmd_set_max_num_packets_per_aggregation)
            print(f"MONITOR switching to throughput={mbps} Kbps delay={delay:.6f}s pps={pps:.2f}")
            last_throughput = mbps

        fullness = read_queue_fullness()
        # print(f"QUEUE_FULLNESS={fullness}")

        if fullness is not None and fullness == 1:
            consecutive_full += 1
        else:
            consecutive_full = 0

        # if queue full reported twice consecutively, signal sender to advance
        if consecutive_full >= 2:
            try:
                tmp = args.signal_file + ".tmp"
                with open(tmp, "w") as f:
                    f.write("full\n")
                os.replace(tmp, args.signal_file)
                print("MONITOR wrote 'full' signal to sender")
            except Exception as e:
                print(f"MONITOR failed to write signal: {e}")
            consecutive_full = 0

            try:
                max_num_packets_per_aggregation += 4
                cmd_set_max_num_packets_per_aggregation = f"echo 'register_write sw_ingress_control.max_num_packets_per_aggregation 0 {max_num_packets_per_aggregation}' | psa_switch_CLI --thrift-ip localhost --thrift-port 9091"
                os.system(cmd_set_max_num_packets_per_aggregation)
                print(f"MONITOR incremented max_num_packets_per_aggregation to {max_num_packets_per_aggregation}")
                time.sleep(1.5)
            except Exception as e:
                print(f"MONITOR failed to increment max_num_packets_per_aggregation: {e}")
                break

        elapsed = time.time() - start
        sleep_time = max(0, delay - elapsed)
        time.sleep(sleep_time)
    
    with open(tmp, "w") as f:
        f.write("finished\n")

if __name__ == "__main__":
    main()
