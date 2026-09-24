import os
import re
from pathlib import Path
from mininet.topo import Topo


SCRIPT_DIR = Path(__file__).resolve().parent
print("Script directory:", SCRIPT_DIR)
MININET_ROOT = SCRIPT_DIR.parent
print("Mininet root directory:", MININET_ROOT)
REPO_ROOT = MININET_ROOT.parent
print("Repository root directory:", REPO_ROOT)

SWITCH_BINARIES = {
    ("psa", True): "psa_switch_grpc",
    ("psa", False): "psa_switch",
    ("v1model", True): "simple_switch_grpc",
    ("v1model", False): "simple_switch",
}


def _resolve_existing_path(path, search_root):
    candidate = Path(path)
    if candidate.is_absolute():
        if candidate.exists():
            return str(candidate)
        raise FileNotFoundError(f"Path does not exist: {path}")

    resolved = (search_root / path).resolve()
    if resolved.exists():
        return str(resolved)

    raise FileNotFoundError(f"Cannot resolve path: {path}")


def _parse_node(node_name):
    if "-p" not in node_name:
        return node_name, None
    base, port = node_name.split("-p", 1)
    if not port.isdigit():
        raise ValueError(f"Invalid port in link endpoint '{node_name}'")
    return base, int(port)


def _numeric_suffix(name, default=0):
    match = re.search(r"(\d+)$", name)
    return int(match.group(1)) if match else default


def _binary_for_switch(switch_spec):
    arch = switch_spec.get("arch")
    grpc_enable = bool(switch_spec.get("grpc_enable", False))
    key = (arch, grpc_enable)
    if key not in SWITCH_BINARIES:
        raise ValueError(f"Unsupported switch configuration: arch={arch!r}, grpc_enable={grpc_enable!r}")
    return SWITCH_BINARIES[key]


class BuildTopo(Topo):
    def __init__(self, topology, log_dir, pcap_dir=None, **opts):
        super().__init__(**opts)
        self.log_dir = log_dir
        self.pcap_dir = pcap_dir
        self.host_names = list(topology.get("hosts", []))
        self.switch_specs = {sw["name"]: sw for sw in topology.get("switches", [])}

        self._add_switches()
        self._add_hosts_and_links(topology.get("links", []))

    def _add_switches(self):
        for switch_name, switch_spec in self.switch_specs.items():
            switch_params = {
                "sw_path": _binary_for_switch(switch_spec),
                "log_file": os.path.join(self.log_dir, f"{switch_name}.log"),
                "log_console": True,
            }
            if self.pcap_dir is not None:
                switch_params["pcap_dump"] = self.pcap_dir
            if switch_spec.get("thrift_port") is not None:
                switch_params["thrift_port"] = switch_spec["thrift_port"]
            if switch_spec.get("grpc_port") is not None:
                switch_params["grpc_port"] = switch_spec["grpc_port"]
            if switch_spec.get("pipeline_config"):
                switch_params["json_path"] = _resolve_existing_path(
                    switch_spec["pipeline_config"],
                    REPO_ROOT,
                )
            self.addSwitch(switch_name, **switch_params)

    def _add_hosts_and_links(self, links):
        h2s_links = {}
        switch_links = []
        host_params_by_name = {}
        for raw in links:
            if len(raw) < 2:
                raise ValueError(f"Invalid link entry: {raw!r}")
            left_node, left_port = _parse_node(raw[0])
            right_node, right_port = _parse_node(raw[1])

            if left_node[0] == "h" and right_node[0] == "s":
                node1, port1, node2, port2 = left_node, left_port, right_node, right_port
            else:
                # if (right_node[0] == "h" and left_node[0] == "s")
                # || (right_node[0] == "s" and left_node[0] == "s")
                # || (right_node[0] == "h" and left_node[0] == "h")
                node1, port1, node2, port2 = right_node, right_port, left_node, left_port

            link = {
                "node1": node1,
                "node2": node2,
                "node1_port": port1,
                "node2_port": port2,
                "latency": "0ms",
                "bandwidth": None,
            }
            if len(raw) > 2:
                link["latency"] = self._format_latency(raw[2])
            if len(raw) > 3:
                link["bandwidth"] = raw[3]

            if link["node1"][0] == "h" and link["node2"][0] == "s":
                h2s_links[link["node1"]] = link
            else:
                switch_links.append(link)

        h2s_links = dict(sorted(h2s_links.items(), key=lambda item: item[0]))
        switch_links.sort(key=lambda item: item["node1"] + item["node2"])

        for host_name in self.host_names:
            host_id = _numeric_suffix(host_name, default=self.host_names.index(host_name) + 1)
            h2s_link = h2s_links.get(host_name)
            switch_name = h2s_link["node2"] if h2s_link else None
            switch_id = _numeric_suffix(switch_name, default=1) if switch_name else 1
            host_params_by_name[host_name] = {
                "ip": f"10.0.{switch_id}.{host_id}/16",
                "mac": f"00:00:00:00:00:{host_id:02x}",
            }
            self.addHost(host_name, **host_params_by_name[host_name])

        for host_name, link in h2s_links.items():
            switch_name = link["node2"]

            link_params = {
                "delay": link["latency"],
                "bw": link["bandwidth"],
                "addr1": host_params_by_name[host_name]["mac"],
            }
            if link["node2_port"] is not None:
                link_params["port2"] = link["node2_port"]
            self.addLink(host_name, switch_name, **link_params)

        for link in switch_links:
            link_params = {
                "delay": link["latency"],
                "bw": link["bandwidth"],
            }
            if link["node1_port"] is not None:
                link_params["port1"] = link["node1_port"]
            if link["node2_port"] is not None:
                link_params["port2"] = link["node2_port"]
            self.addLink(link["node1"], link["node2"], **link_params)

    @staticmethod
    def _format_latency(latency):
        return latency if isinstance(latency, str) else f"{latency}ms"


