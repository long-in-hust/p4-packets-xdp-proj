BUILD_DIR = build
SRC_DIR = src
LOG_DIR = logs
LOGS_DEVICES_DIR = $(LOG_DIR)/devices
PCAP_DIR = pcap

P4C = p4c-bm2-psa
P4C_DPDK = p4c-dpdk
P4C_EBPF = p4c-ebpf
MININET = /home/p4/src/p4dev-python-venv/bin/mn
PYTHON = /home/p4/src/p4dev-python-venv/bin/python
P4C_ARGS_AGG = --p4runtime-format text
P4C_ARGS_SPL = --p4runtime-files $(BUILD_DIR)/l4_split.p4info.txtpb --p4runtime-format text
source := $(wildcard $(SRC_DIR)/*.p4)
P4_FILES := $(notdir $(source))

compiled_json := $(P4_FILES:%.p4=$(BUILD_DIR)/%.json)

all: build load_ctrl_plane

run:
	@echo "Running L2 Aggregator with PSA switch..."
	cd mininet ; sudo ./run_mininet.py --topo topology.json

run_simple:
	@echo "Running Simple Forwarder with PSA switch..."
	cd mininet ; sudo ./run_emu.py -j ../$(BUILD_DIR)/simple.json -b psa_switch

build_aggregator:	dirs $(compiled_json)
	@echo "---------------------------------"
	@echo "Building L2 Aggregator..."
	mkdir -p $(BUILD_DIR)/bmv2
	$(P4C) --p4v 16 $(P4C_ARGS_AGG) --arch psa -o $(BUILD_DIR)/bmv2/l4_aggregate.json \
		--p4runtime-files $(BUILD_DIR)/bmv2/l4_aggregate.p4info.txtpb src/aggregator/main.p4
	@echo "Building Succeeded..."

build_aggregator_dpdk:	dirs $(compiled_json)
	@echo "---------------------------------"
	@echo "Compiling L4 Aggregator to C code..."
	mkdir -p $(BUILD_DIR)/dpdk
	$(P4C_DPDK) --p4v 16 $(P4C_ARGS_AGG) --arch psa -o $(BUILD_DIR)/dpdk/l4_aggregate.spec \
		--p4runtime-files $(BUILD_DIR)/dpdk/l4_aggregate.p4info.txtpb src/aggregator/main.p4
	
	@echo "Building Succeeded..."

build_aggregator_ebpf:	dirs $(compiled_json)
	@echo "---------------------------------"
	@echo "Compiling L4 Aggregator to C code..."
	mkdir -p $(BUILD_DIR)/ebpf
	$(P4C_EBPF) --p4v 16 $(P4C_ARGS_AGG) --arch psa \
		--emit-externs -o $(BUILD_DIR)/ebpf/l4_aggregate.c \
		--p4runtime-files $(BUILD_DIR)/ebpf/l4_aggregate.p4info.txtpb src/aggregator/main.p4
	@echo "Compiling to object..."
	make -f /home/p4/src/p4c/backends/ebpf/runtime/kernel.mk \
		BPFOBJ=$(BUILD_DIR)/ebpf/l4_aggregate.o P4FILE=src/aggregator/main.p4
	@echo "Building Succeeded..."

build_aggregator_ir:	dirs $(compiled_json)
	@echo "---------------------------------"
	@echo "Building L2 Aggregator..."
	mkdir -p $(BUILD_DIR)/bmv2
	$(P4C) --p4v 16 $(P4C_ARGS_AGG) --arch psa -o $(BUILD_DIR)/bmv2/l4_aggregate.json \
		--toJSON $(BUILD_DIR)/bmv2/l4_aggregate_ir.json \
		--p4runtime-files $(BUILD_DIR)/bmv2/l4_aggregate.p4info.txtpb src/aggregator/main.p4
	@echo "Building Succeeded..."

build_aggregator_dpdk_ir:	dirs $(compiled_json)
	@echo "---------------------------------"
	@echo "Building L2 Aggregator..."
	mkdir -p $(BUILD_DIR)/dpdk
	$(P4C_DPDK)  --p4v 16 $(P4C_ARGS_AGG) --arch psa -o $(BUILD_DIR)/dpdk/l4_aggregate.spec \
		--toJSON $(BUILD_DIR)/dpdk/l4_aggregate_ir.json \
		--p4runtime-files $(BUILD_DIR)/dpdk/l4_aggregate.p4info.txtpb src/aggregator/main.p4
	@echo "Building Succeeded..."

build_simple:	dirs $(compiled_json)
	@echo "---------------------------------"
	@echo "Building Simple Forwarder..."
	$(P4C) --p4v 16 --arch psa -o $(BUILD_DIR)/simple.json src/simple/main.p4
	@echo "Building Succeeded..."

build: build_aggregator build_simple

dirs:
	mkdir -p $(BUILD_DIR) $(LOG_DIR) $(LOGS_DEVICES_DIR) $(PCAP_DIR)

stop:
	sudo $(MININET) -c

cleanbuild:
	rm -rf $(BUILD_DIR)

clean: stop
	rm -rf $(BUILD_DIR)

cleanall: stop
	rm -rf $(BUILD_DIR) $(LOG_DIR) $(LOGS_DEVICES_DIR) $(PCAP_DIR)