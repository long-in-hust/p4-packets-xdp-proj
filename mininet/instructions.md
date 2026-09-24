# Hướng dẫn tạo kịch bản Mininet (cho prompt)

Thư mục hiện tại : mininet/

## Miêu tả chức năng

- Tạo một kịch bản Mininet theo JSON topology được cung cấp. (tham số đầu vào là "--topo <tên file JSON>")

- JSON topo có dạng như sau:

```json
{
    "hosts": [
        "h1",
        "h2"
    ],
    "switches": [
        {
            "name": "s1",
            "data_plane_ports": [
                "s1-p1",
                "s1-p2"
            ],
            "arch": "psa",
            "grpc_enable": true,
            "thrift_port": 9001,
            "grpc_port": 50051,
            "pipeline_config": "build/psa_switch_grpc.json"
        }
    ],
    "links": [
        ["h1", "s1-p1"], ["s1-p2", "h2"]
    ]
}
```

- Nếu `grpc_enable` là `true`, thì switch sẽ được khởi tạo với cả giao diện gRPC và Thrift. Nếu `grpc_enable` là `false`, switch sẽ được khởi tạo chỉ với giao diện Thrift.

- Nếu `arch` là `"psa"`, switch sẽ được khởi tạo với kiến trúc PSA. Nếu `arch` là `"v1model"`, switch sẽ được khởi tạo với kiến trúc v1model.

- File thực thi có thể được sử dụng cho từng trường hợp như sau:
  - grpc_enable = true, arch = "psa": `psa_switch_grpc`
  - grpc_enable = false, arch = "psa": `psa_switch`
  - grpc_enable = true, arch = "v1model": `simple_switch_grpc`
  - grpc_enable = false, arch = "v1model": `simple_switch`

- `data_plane_ports` là danh sách các cổng dữ liệu của switch. Mỗi cổng dữ liệu sẽ được kết nối với một host hoặc một switch khác thông qua `links`.

- `pipeline_config` là đường dẫn đến file JSON cấu hình pipeline của switch. File này sẽ được sử dụng để nạp vào switch khi khởi tạo. Nếu `pipeline_config` không được cung cấp, switch sẽ được khởi tạo mà không có cấu hình pipeline (sử dụng tham số `--no-p4`).

- Mã nguồn chính của mạng triển khai mininet đặt tại `run_mininet.py` (dựa trên file run_emu.py hiện có), lớp host nằm trong `includes/mininet_host.py` và lớp switch nằm trong `includes/p4_switches.py`.

- Dựa trên mã nguồn gốc, làm gọn mã và sửa một cách cực đoan nhất có thể để tuân theo yêu cầu ở trên.

- Cấu trúc mã nguồn:

```text
mininet/     # thư mục hiện hành
├── run_mininet.py
├── logs/  # thư mục chứa các file log
├── pcap/  # thư mục chứa các file pcap
└── includes/
    ├── netstat.py  # các hàm tiện ích để lấy thông tin mạng
    ├── mininet_host.py  # các lớp host p4
    ├── p4_switches.py  # các lớp switch p4
    └── network.py  # mô hình mạng (bao gồm hosts, switches (trong file p4_switches.py), links)
```

## Xuất file

- Logs sẽ được xuất ra file `<switch_name>.log` trong thư mục `logs/`.

- PCAP của các giao diện trên các host lẫn switches sẽ được xuất ra file `<interface_name>.pcap` trong thư mục `pcap/`.
