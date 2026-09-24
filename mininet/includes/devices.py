import logging
import os
import tempfile
from sys import exit
import psutil
from time import sleep

from mininet.log import error, info
from mininet.moduledeps import pathCheck
from mininet.node import Switch
from mininet.node import Host

def check_listening_on_port(port):
    for c in psutil.net_connections(kind='inet'):
        if c.status == 'LISTEN' and c.laddr[1] == port:
            return True
    return False

SWITCH_START_TIMEOUT = 20 # seconds

class P4Host(Host):
    def config(self, **params):
        r = super(Host, self).config(**params)

        self.defaultIntf().rename("eth0")

        for off in ["rx", "tx", "sg"]:
            cmd = "/sbin/ethtool --offload eth0 %s off" % off
            self.cmd(cmd)

        # disable IPv6
        self.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")
        self.cmd("sysctl -w net.ipv6.conf.default.disable_ipv6=1")
        self.cmd("sysctl -w net.ipv6.conf.lo.disable_ipv6=1")

        return r

	## Unused method
    # def describe(self):
    #     print ("**********")
    #     print (self.name)
    #     print ("default interface: %s\t%s\t%s" % (
    #         self.defaultIntf().name,
    #         self.defaultIntf().IP(),
    #         self.defaultIntf().MAC()
    #     ))
    #     print ("**********")


class P4Switch(Switch):
	"""P4 virtual switch with BMv2 backend and gRPC control plane interface"""
	device_id = 0
	next_grpc_port = 50051
	next_thrift_port = 9091

	def __init__(self, name, sw_path = None, json_path = None,
				 thrift_port = None,
				 grpc_port = None,
				 pcap_dump = None,
				 log_console = False,
				 verbose = False,
				 device_id = None,
				 enable_debugger = False,
				 **kwargs):
		logging.info("Initializing P4Switch: %s", name)
		logging.debug("sw_path: %s, json_path: %s, grpc_port: %s, thrift_port: %s", sw_path, json_path, grpc_port, thrift_port)
		Switch.__init__(self, name, **kwargs)
		self.sw_path = sw_path
		self.uses_grpc = 'grpc' in os.path.basename(sw_path)
		pathCheck(sw_path)

		if json_path is not None:
			if not os.path.isfile(json_path):
				error("Invalid JSON file.\n")
				exit(1)
			self.json_path = json_path
		else:
			self.json_path = None

		if grpc_port is not None:
			self.grpc_port = grpc_port
		else:
			self.grpc_port = P4Switch.next_grpc_port
			logging.debug("Assigning grpc_port: %d", self.grpc_port)
			P4Switch.next_grpc_port += 1

		if self.uses_grpc and check_listening_on_port(self.grpc_port):
			error('%s cannot bind gRPC port %d because it is bound by another process\n' % (self.name, self.grpc_port))
			exit(1)

		if thrift_port is not None:
			self.thrift_port = thrift_port
		else:
			self.thrift_port = P4Switch.next_thrift_port
			logging.debug("Assigning thrift_port: %d", self.thrift_port)
			P4Switch.next_thrift_port += 1

		if check_listening_on_port(self.thrift_port):
			error('%s cannot bind port %d because it is bound by another process\n' % (self.name, self.thrift_port))
			exit(1)

		self.verbose = verbose
		provided_log = kwargs.get('log_file')
		if provided_log:
			logfile = provided_log
		else:
			default_logs_dir = os.path.join(os.getcwd(), 'logs', 'devices')
			os.makedirs(default_logs_dir, exist_ok=True)
			logfile = os.path.join(default_logs_dir, 'p4s.{}.log'.format(self.name))
		os.makedirs(os.path.dirname(logfile), exist_ok=True)
		self.output = open(logfile, 'a')
		self.logfile = logfile
		self.pcap_dump = pcap_dump
		self.enable_debugger = enable_debugger
		self.log_console = log_console
		if device_id is not None:
			self.device_id = device_id
			P4Switch.device_id = max(P4Switch.device_id, device_id)
		else:
			self.device_id = P4Switch.device_id
			P4Switch.device_id += 1

		self.nanomsg = "ipc:///tmp/bm-{}-log.ipc".format(self.device_id)

	def check_switch_started(self, pid):
		listen_port = self.grpc_port if self.uses_grpc else self.thrift_port
		for _ in range(SWITCH_START_TIMEOUT * 2):
			if not os.path.exists(os.path.join("/proc", str(pid))):
				logging.warning("Process %d is either terminated or not running at all.", pid)
				return False
			if check_listening_on_port(listen_port):
				return True
			sleep(0.5)

	def start(self, controllers):
		logging.info("Starting P4 switch {}.\n".format(self.name))
		args = [self.sw_path]
		for port, intf in self.intfs.items():
			if not intf.IP():
				args.extend(['-i', str(port) + "@" + intf.name])
		if self.pcap_dump:
			logging.debug("Enabling pcap dump for switch: %s", self.name)
			args.append("--pcap=%s" % self.pcap_dump)
			logging.debug("Pcap dump enabled.")
		if self.nanomsg:
			logging.debug("Using nanomsg endpoint: %s", self.nanomsg)
			args.extend(['--nanolog', self.nanomsg])
			logging.debug("Nanomsg endpoint set up.")
		args.extend(['--device-id', str(self.device_id)])
		# P4Switch.device_id += 1
		logging.debug("Assigned device_id: %d", self.device_id)
		if self.json_path:
			logging.debug("Using JSON file: %s", self.json_path)
			args.append(self.json_path)
		else:
			if self.uses_grpc:
				logging.info("gRPC switch %s starting in control-plane mode (no P4 JSON)", self.name)
			else:
				logging.debug("No JSON file provided. Continuing without it.")
			args.append("--no-p4")
		if self.enable_debugger:
			logging.debug("Enabling debugger for switch: %s", self.name)
			args.append("--debugger")
		if self.log_console:
			logging.debug("Enabling console logging for switch: %s", self.name)
			args.append("--log-console")
		if self.thrift_port:
			logging.debug("Using Thrift port: %d", self.thrift_port)
			args.extend(['--thrift-port', str(self.thrift_port)])
		if self.uses_grpc and self.grpc_port:
			logging.debug("Using gRPC port: %d", self.grpc_port)
			args.extend(['--', '--grpc-server-addr', '0.0.0.0:' + str(self.grpc_port)])
		if self.uses_grpc:
			args.extend(['--cpu-port', str(510)])

		cmd = ' '.join(args)
		info(cmd + "\n")

		logfile = getattr(self, 'logfile', None)
		if not logfile:
			default_logs_dir = os.path.join(os.getcwd(), 'logs', 'devices')
			os.makedirs(default_logs_dir, exist_ok=True)
			logfile = os.path.join(default_logs_dir, 'p4s.{}.log'.format(self.name))
		with tempfile.NamedTemporaryFile() as f:
			self.cmd(cmd + ' >>' + logfile + ' 2>&1 & echo $! >> ' + f.name)
			pid = int(f.read())
		logging.debug("P4 switch {} PID is {}.\n".format(self.name, pid))
		if not self.check_switch_started(pid):
			logging.error("P4 switch {} did not start correctly.\n".format(self.name))
			exit(1)
		logging.info("P4 switch {} has been started.\n".format(self.name))

	def stop(self):
		"Terminate P4 switch."
		self.output.flush()
		self.cmd('kill %' + self.sw_path)
		self.cmd('wait')
		self.deleteIntfs()
