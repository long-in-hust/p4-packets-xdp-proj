import subprocess

def build_register_entries():
    entries = []
    # Các phần tử trong reg array pool_save_pos
    for pool_index in range(0, 64):
        entries.append({
                    "register_name": "sw_ingress_control.available_pools",
                    "index": pool_index,
                    "value": 12,
        })
        entries.append({
            "register_name": "sw_ingress_control.occupancy_bitmaps",
            "index": pool_index,
            "value": 0,
        })
        
    for list_index in range(0, 128):
        entries.append({
            "register_name": "sw_ingress_control.pkt_occupied",
            "index": list_index,
            "value": 0,
        })
        entries.append({
            "register_name": "sw_ingress_control.pkt_data_sizes",
            "index": list_index,
            "value": 0,
        })

    entries.append({
        "register_name": "sw_ingress_control.pkt_save_pos",
        "index": 0,
        "value": 0,
    })

    entries.append({
        "register_name": "sw_ingress_control.pkt_read_pos",
        "index": 0,
        "value": 0,
    })

    entries.append({
        "register_name": "sw_ingress_control.pool_save_pos",
        "index": 0,
        "value": 2,
    })

    return entries


def write_registers(thrift_ip, thrift_port, register_entries):
    # register read/write qua P4Runtime currently unsupported on this target,
    # so use BMv2/PSA thrift CLI for register updates.
    cli_cmd = [
        "psa_switch_CLI",
        "--thrift-port",
        str(thrift_port),
        "--thrift-ip",
        str(thrift_ip),
    ]

    for entry in register_entries:
        register_name = entry["register_name"]
        index = entry["index"]
        value = entry["value"]

        
        cli_input = f"register_write {register_name} {index} {value}\n"

        try:
            result = subprocess.run(
                cli_cmd,
                input=cli_input,
                text=True,
                capture_output=True,
                check=True,
            )
            print(
                f"Đã gửi lệnh register_write qua thrift: {register_name}[{index}] = {value}"
            )
        except subprocess.CalledProcessError as exc:
            print(
                f"Lỗi khi ghi register qua thrift cho {register_name}[{index}] = {value}"
            )
            raise exc
        except FileNotFoundError as exc:
            print("Không tìm thấy lệnh psa_switch_CLI trong PATH")
            raise exc