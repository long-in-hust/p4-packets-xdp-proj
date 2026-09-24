#!/bin/bash

throughput=20000  # bits per second

while true; do
    echo 'register_read sw_ingress_control.queue_is_full 0' | psa_switch_CLI --thrift-ip localhost --thrift-port 9091
    echo 'register_read sw_ingress_control.byte_saved_total 0' | psa_switch_CLI --thrift-ip localhost --thrift-port 9091
    sleep $((1/throughput*77/8))  # Adjust sleep time based on desired throughput
done