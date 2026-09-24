#!/home/p4/src/p4dev-python-venv/bin/python
import argparse
import os

from includes.runner import JsonMininetRunner


def get_args():
    cwd = os.getcwd()
    parser = argparse.ArgumentParser()
    parser.add_argument("-q", "--quiet", action="store_true", default=False, help="Suppress log messages.")
    parser.add_argument("-t", "--topo", required=False, default=os.path.join(cwd, "topology.json"), help="Path to topology JSON.")
    parser.add_argument("-l", "--log-dir", required=False, default=os.path.join(cwd, "logs"), help="Directory for switch logs.")
    parser.add_argument("-p", "--pcap-dir", required=False, default=os.path.join(cwd, "pcap"), help="Directory for pcap output.")
    return parser.parse_args()


if __name__ == "__main__":
    args = get_args()
    JsonMininetRunner(args.topo, args.log_dir, args.pcap_dir, args.quiet).run()