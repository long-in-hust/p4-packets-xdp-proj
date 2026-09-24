# Thư viện dựng mã protobuf cho P4Runtime
import p4.v1.p4runtime_pb2 as p4runtime_pb2
# Module entities.py chứa hàm get_id_from_name để hỗ trợ lấy ID của table, action, match field từ p4info
from .entities import get_id_from_name, get_match_field_id
import time

def build_table_entry(p4info, table_name, match_fields, field_byte_lens, action_name, param=None):
    table_id = get_id_from_name(p4info, table_name, "table")
    action_id = get_id_from_name(p4info, action_name, "action")

    tbl_entity = p4runtime_pb2.Entity()
    tbl_entity.table_entry.table_id = table_id

    if len(field_byte_lens) != len(match_fields):
        raise ValueError("field_byte_lens must contain one length per match field")

    for field_index, (field_name, field_value) in enumerate(match_fields.items()):
        match_field = tbl_entity.table_entry.match.add()
        match_field.field_id = get_match_field_id(p4info, table_name, field_name)
        if field_value["type"] == "EXACT":
            match_field.exact.value = field_value["value"].to_bytes(
                field_byte_lens[field_index], byteorder='big'
            )

    action = tbl_entity.table_entry.action.action
    action.action_id = action_id

    if param:
        action_param = action.params.add()
        action_param.param_id = 1  # Assuming the action has one parameter with ID
        action_param.value = param.to_bytes(2, byteorder='big')

    return tbl_entity

def write_bitmap_lookup_table_entries(p4info, client_stub, device_id=0, role=0, election_id_high=0, election_id_low=1):
    def get_bit(value, index):
        return (value >> index) & 1

    for lookup_bitmap in range(0, 2048):
        free_bits = [i for i in range(0, 12) if get_bit(lookup_bitmap, i) == 0]
        for length in range(1, 13):
            if len(free_bits) >= length:
                chosen   = free_bits[0 : length]
                operation_bitmap = 0
                for pos in chosen:
                    operation_bitmap |= (1 << pos)
                # Do something with the generated bitmap value, e.g., write it to the table
                match_fields = {
                    "meta.occupancy_bitmap": 
                    {
                        "type": "EXACT", 
                        "value": lookup_bitmap
                    },
                    "meta.no_of_pools": {
                        "type": "EXACT",
                        "value": length
                    }
                }
                tbl_entry = build_table_entry(
                    p4info,
                    "sw_ingress_control.lookup",
                    match_fields,
                    [2, 2],
                    "sw_ingress_control.get_operation_bitmap",
                    operation_bitmap
                )
                # Here you would typically send tbl_entry to the switch using a write request
                request = p4runtime_pb2.WriteRequest()
                request.device_id = device_id  # ID của thiết bị switch
                request.role_id = role
                request.election_id.high = election_id_high
                request.election_id.low = election_id_low
                request.updates.add(type=p4runtime_pb2.Update.INSERT, entity=tbl_entry)
                print(f"Writing TableEntry for lookup_bitmap={lookup_bitmap}, length={length}, operation_bitmap={operation_bitmap}")
                client_stub.Write(request)

def write_pool_table_entries(p4info, client_stub, device_id=0, role=0, election_id_high=0, election_id_low=1):
    for pool_index in range(0, 12):
        # Gói nhỏ lưu vào mỗi pool
        save_match_fields = {
            "meta.is_aggregation": {
                "type": "EXACT",
                "value": 0
            },
            "meta.pool_bitmap": {
                "type": "EXACT",
                "value": 1
            }
        }
        save_tbl_entry = build_table_entry(
            p4info,
            f"sw_ingress_control.ops_pool_{pool_index}",
            save_match_fields,
            [2, 2],
            f"sw_ingress_control.save_pool_{pool_index}"
        )
        save_request = p4runtime_pb2.WriteRequest()
        save_request.device_id = device_id  # ID của thiết bị switch
        save_request.role_id = role
        save_request.election_id.high = election_id_high
        save_request.election_id.low = election_id_low
        save_request.updates.add(type=p4runtime_pb2.Update.INSERT, entity=save_tbl_entry)
        print(f"Writing save TableEntry for pool_index={pool_index}")
        client_stub.Write(save_request)

        # Gói làm việc tổng hợp đọc từ mỗi pool
        read_match_fields = {
            "meta.is_aggregation": {
                "type": "EXACT",
                "value": 1
            },
            "meta.pool_bitmap": {
                "type": "EXACT",
                "value": 1
            }
        }
        read_tbl_entry = build_table_entry(
            p4info,
            f"sw_ingress_control.ops_pool_{pool_index}",
            read_match_fields,
            [2, 2],
            f"sw_ingress_control.read_pool_{pool_index}"
        )
        read_request = p4runtime_pb2.WriteRequest()
        read_request.device_id = device_id  # ID của thiết bị switch
        read_request.role_id = role
        read_request.election_id.high = election_id_high
        read_request.election_id.low = election_id_low
        read_request.updates.add(type=p4runtime_pb2.Update.INSERT, entity=read_tbl_entry)
        print(f"Writing read TableEntry for pool_index={pool_index}")
        client_stub.Write(read_request)

def write_append_stack_table_entries(p4info, client_stub, device_id=0, role=0, election_id_high=0, election_id_low=1):
    for stack_index in range(1, 13):
        match_fields = {
            "meta.no_of_pools": {
                "type": "EXACT",
                "value": stack_index
            }
        }
        tbl_entry = build_table_entry(
            p4info,
            "sw_ingress_control.append_stack",
            match_fields,
            [1],
            f"sw_ingress_control.append_stack_idx_{stack_index}"
        )
        request = p4runtime_pb2.WriteRequest()
        request.device_id = device_id  # ID của thiết bị switch
        request.role_id = role
        request.election_id.high = election_id_high
        request.election_id.low = election_id_low
        request.updates.add(type=p4runtime_pb2.Update.INSERT, entity=tbl_entry)
        print(f"Writing TableEntry for append_stack with stack_index={stack_index}")
        client_stub.Write(request)