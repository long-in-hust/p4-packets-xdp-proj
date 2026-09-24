#!/usr/bin/python3

import time
import argparse
import os


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
    parser.add_argument("--control-file", default="./tests_control.txt", help="path for control messages")
    parser.add_argument("--duration", type=float, default=18000.0, help="maximum total run duration in seconds")
    parser.add_argument("--signal-file", default="./tests_signal.txt", help="path where monitor writes fullness signals")
    args = parser.parse_args()

    max_num_packets_per_aggregation = 3
    kept = False
    
    cmd_reload_device = "python3 ../ctrl_plane/p4runtime_api/agg_switch.py --p4info ../build/l4_aggregate.p4info.txtpb --bmv2-json ../build/l4_aggregate.json"
    tmp = args.signal_file + ".tmp"

    end_time = time.time() + args.duration
    last_throughput = None
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

        # check for increment signal from sender
        sig_from_sender = read_and_clear_signal(args.signal_file)
        if sig_from_sender and sig_from_sender.lower().startswith("increment"):
            try:
                max_num_packets_per_aggregation += 4
                
                if max_num_packets_per_aggregation > 43:
                    print("MONITOR reached the maximum worker packet limit, exiting")
                    break

                cmd_set_max_num_packets_per_aggregation = f"echo 'register_write sw_ingress_control.max_num_packets_per_aggregation 0 {max_num_packets_per_aggregation}' | psa_switch_CLI --thrift-ip localhost --thrift-port 9091"

                os.system(cmd_reload_device)
                os.system(cmd_set_max_num_packets_per_aggregation)
                print(f"MONITOR received 'increment' and set max_num_packets_per_aggregation to {max_num_packets_per_aggregation}")
                time.sleep(3)
            except Exception as e:
                print(f"MONITOR failed to apply increment: {e}")

        # follow sender's announced throughput and delay
        mbps = int(float(ctrl.get("throughput", 0)))
        delay = float(ctrl.get("delay", 0.1))
        pps = float(ctrl.get("pps", 0))
        if last_throughput != mbps:
            print(f"MONITOR switching to throughput={mbps} Kbps delay={delay:.6f}s pps={pps:.2f}")
            last_throughput = mbps

        # (Queue fullness is detected by the sender via the log; monitor no longer polls the register.)

        elapsed = time.time() - start
        sleep_time = max(0, delay - elapsed)
        time.sleep(sleep_time)
    
    with open(tmp, "w") as f:
        f.write("finished\n")

if __name__ == "__main__":
    main()
