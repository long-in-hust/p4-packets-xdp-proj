import json
import os
import subprocess
from pathlib import Path
from time import sleep

from .devices import P4Host
from .devices import P4Switch
from .network import BuildTopo

from mininet.cli import CLI
from mininet.link import TCLink
from mininet.net import Mininet

class JsonMininetRunner:
    def __init__(self, topo_file, log_dir, pcap_dir, quiet=False):
        self.quiet = quiet
        self.topo_path = Path(topo_file).resolve()
        self.log_dir = str(Path(log_dir).resolve())
        self.pcap_dir = str(Path(pcap_dir).resolve())

        self._clear_old_outputs()

        with open(self.topo_path, "r", encoding="utf-8") as handle:
            self.topology = json.load(handle)

        self.hosts = self.topology.get("hosts", [])
        self.switches = {sw["name"]: sw for sw in self.topology.get("switches", [])}
        self.links = self.topology.get("links", [])

        for directory in (self.log_dir, self.pcap_dir):
            os.makedirs(directory, exist_ok=True)

    def _clear_old_outputs(self):
        for directory in (self.log_dir, self.pcap_dir):
            path = Path(directory)
            path.mkdir(parents=True, exist_ok=True)
            for child in path.iterdir():
                if child.is_file() or child.is_symlink():
                    child.unlink()
                elif child.is_dir():
                    for nested in sorted(child.rglob('*'), reverse=True):
                        if nested.is_file() or nested.is_symlink():
                            nested.unlink()
                        elif nested.is_dir():
                            nested.rmdir()
                    child.rmdir()

    def logger(self, *items):
        if not self.quiet:
            print(" ".join(str(item) for item in items))

    def create_network(self):
        self.logger("Building mininet topology.")
        self.topo = BuildTopo(self.topology, self.log_dir, self.pcap_dir)
        self.net = Mininet(
            topo=self.topo,
            link=TCLink,
            host=P4Host,
            switch=P4Switch,
            controller=None,
        )

    def program_hosts(self):
        for host_name in self.topo.hosts():
            host = self.net.get(host_name)
            host.defaultIntf().rename(f"{host_name}-eth0")

    def do_cli(self):
        self.logger("Starting mininet CLI")
        print("")
        print("======================================================================")
        print("Welcome to the Mininet CLI!")
        print("======================================================================")
        print("The switches are running with the topology described by the JSON file.")
        print("")
        print(f"Logs: {self.log_dir}")
        print(f"PCAP: {self.pcap_dir}")
        print("")
        CLI(self.net)
    
    def run(self):
        self.create_network()
        self.net.start()
        sleep(1)
        self.program_hosts()
        sleep(1)
        self.do_cli()
        self.net.stop()