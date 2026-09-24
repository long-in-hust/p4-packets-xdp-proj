#!/usr/bin/env python3

# Thư viện giao tiếp bằng giao thức gRPC
import time

import grpc
# thư viện dịch protobuf thành văn bản
import google.protobuf.text_format

# Thư viện dựng mã protobuf cho P4Runtime
import p4.v1.p4runtime_pb2 as p4runtime_pb2
# Thư viện dựng client và server cho gRPC, trong trường hợp này là client
# để giao tiếp với server gRPC trên switch P4
import p4.v1.p4runtime_pb2_grpc as p4runtime_pb2_grpc
# Thư viện hỗ trợ dịch p4info thành protobuf
import p4.config.v1.p4info_pb2 as p4info_pb2


# Thông tin kết nối đến switch có tên "s1"
SW_MGMT_ADDR = "127.0.0.1" # dùng cho cả gRPC và Thrift
SW_GRPC_PORT = 50051
SW_THRIFT_PORT = 9091
SW_DEVICE_ID = 0
CTRL_ROLE_ID = 0 # 0 là role mặc định, có toàn quyền truy cập pipeline
ELECTION_ID_HIGH = 0
ELECTION_ID_LOW = 1
        

# Cập nhật quyền master cho tiến trình control plane,
# gửi yêu cầu đến switch thông qua queue kết nối với kênh gRPC StreamChannel.
def master_arbitration(req_list, device_id=0, role=0):
    # tạo một đối tượng MasterArbitrationUpdate
    request = p4runtime_pb2.StreamMessageRequest()
    request.arbitration.device_id = device_id
    request.arbitration.role.id = role
    request.arbitration.election_id.high = ELECTION_ID_HIGH
    request.arbitration.election_id.low = ELECTION_ID_LOW
    # thêm yêu cầu cập nhật quyền master đến switch vào danh sách các yêu cầu gửi đến switch
    req_list.append(request)

def set_pipeline_config(client_stub, p4info_path, device_config_path, device_id=0, role=0):
    # khởi tạo một đối tượng P4Info
    p4info_msg = p4info_pb2.P4Info()
    with open(p4info_path, "r") as p4info_file:
        # Chuyển nội dung file p4info từ dạng văn bản thành dạng protobuf 
        # rồi gắn vào đối tượng P4Info
        google.protobuf.text_format.Merge(p4info_file.read(), p4info_msg)

    p4_config_bytes = None
    # đọc file device config (với BMv2 là file JSON)
    with open(device_config_path, "r") as device_config_file:
        # nạp nội dung file device config vào đối tượng P4DeviceConfig
        # mã hoá dạng UTF-8
        p4_config_bytes = device_config_file.read().encode("utf-8")

    # tạo một đối tượng SetForwardingPipelineConfigRequest
    request = p4runtime_pb2.SetForwardingPipelineConfigRequest()
    # gán device_id cho request
    request.device_id = device_id

    # gán role cho request
    # (ĐÂY LÀ CẤU HÌNH TỪ BẢN CŨ VÀ SẼ BỊ NGƯNG HỖ TRỢ,
    # SẼ TÌM HIỂU VỀ TRƯỜNG ROLE MỚI SAU)
    request.role_id = CTRL_ROLE_ID # Tạm thời để role mặc định

    # gắn election ID cho request, với hai dải 64 bit, dải cao và dải thấp
    request.election_id.high = ELECTION_ID_HIGH
    request.election_id.low = ELECTION_ID_LOW
    # gắn loại hành động là VERIFY_AND_COMMIT, 
    # nghĩa là kiểm tra cấu hình pipeline và áp dụng nếu hợp lệ
    # đồng thời xoá các cấu hình pipeline cũ nếu có
    request.action = p4runtime_pb2.SetForwardingPipelineConfigRequest.VERIFY_AND_COMMIT
    # gắn thông tin p4info và device config vào request:
    # 1 - sao chép protobuf từ p4info_msg vào request.config.p4info
    request.config.p4info.CopyFrom(p4info_msg)
    # 2- tuần tự hoá đối tượng P4DeviceConfig thành chuỗi byte\
    # và gán vào request.config.p4_device_config
    request.config.p4_device_config = p4_config_bytes

    # gửi request đến switch thông qua stub gRPC
    client_stub.SetForwardingPipelineConfig(request)

    # in ra thông báo xác nhận
    print(f"Đã gửi yêu cầu SetForwardingPipelineConfig đến switch với device_id={device_id}, role={role}, election_id=({ELECTION_ID_HIGH}, {ELECTION_ID_LOW})")

def main():
    # tạo một kênh gRPC không bảo mật đến switch (dùng cho set pipeline config)
    channel = grpc.insecure_channel(f'{SW_MGMT_ADDR}:{SW_GRPC_PORT}')

    # tạo một stub client P4Runtime để giao tiếp với switch thông qua kênh gRPC
    # stub client được thư viện tự động sinh ra và chỉ cần nạp tham số channel
    stub = p4runtime_pb2_grpc.P4RuntimeStub(channel)

    # Tạo một danh sách chứa các bản tin, được đẩy vào bởi các hàm khác
    # Bản tin sau đó được stream lấy ra và gửi đến switch thông qua
    # kênh gRPC StreamChannel
    requests_list = []

    # Hàm này sẽ liên tục lấy các bản tin từ hàng đợi requests_queue và yield chúng ra
    def request_iterator(input_list):
        while True:
            # lấy phần tử đầu tiên trong danh sách các bản tin được đẩy vào
            # (theo nguyên tắc FIFO), nếu danh sách rỗng thì trả về None
            msg = input_list.pop(0) if input_list else None
            # Nếu danh sách rỗng, tạm dừng 0.01 giây trước khi tiếp tục vòng lặp
            # Nếu để hàm yield về rỗng, stream sẽ bị đóng
            if msg is None:
                time.sleep(0.01)
                continue
            yield msg

    # tạo một kênh stream gRPC để gửi các bản tin đến switch
    # sử dụng stub client và hàng đợi
    # kênh stream được yêu cầu bởi bản tin cập nhật quyền master
    stream = stub.StreamChannel(request_iterator(requests_list))

    master_arbitration(
        req_list=requests_list,
        device_id=SW_DEVICE_ID,
        role=CTRL_ROLE_ID
    )

    for msg in stream:
        if msg.HasField("arbitration"):
            if msg.arbitration.status.code == 0:
                print("Primary granted")
                break
            else:
                print("Not primary:", msg.arbitration.status.message)
                raise RuntimeError("Controller is not primary")

    set_pipeline_config(
        client_stub=stub,
        p4info_path="../../build/l4_aggregate.p4info.txtpb",
        device_config_path="../../build/l4_aggregate.json",
        device_id=SW_DEVICE_ID,
        role=CTRL_ROLE_ID
    )


if __name__ == "__main__":
    main()