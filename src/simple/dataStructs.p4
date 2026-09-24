/*
**************************************************************
Định nghĩa một số kiểu dữ liệu hay dùng và có thể thay đổi kích thước
**************************************************************
*/

typedef bit<32> chunk_t;
typedef bit<8> pool_size_t;
typedef bit<12> saved_size_t;

/*
**************************************************************
Các cấu trúc dữ liệu, header sẽ được parser lưu vào từ buffer gói tin
**************************************************************
*/

header packet_out_t {
    bit<128> payload;
}

header ethernet_t {
    bit<48> dstAddr;
    bit<48> srcAddr;
    bit<16> etherType;
}

header ipv4_t {
    bit<4> version;
    bit<4> ihl;
    bit<8> diffserv;
    bit<16> totalLen;
    bit<16> identification;
    bit<3> flags;
    bit<13> fragOffset;
    bit<8> ttl;
    bit<8> protocol;
    bit<16> hdrChecksum;
    bit<32> srcAddr;
    bit<32> dstAddr;
}

header udp_t {
    bit<16> srcPort;
    bit<16> dstPort;
    bit<16> length;
    bit<16> checksum;
}

header packet_type_t {
    bit<8> type_field;
}

header padding_len_t {
    bit<8> plen;
}

header padding_t {
    varbit<120> padding_bytes;
}

header aggregation_t {
    bit<16> num;
    bit<16> len;
}

header msg_length_t {
    bit<8> len;
}

header msg_t {
    chunk_t msg;
}

struct hdr_structures_t {
    packet_out_t PacketOut;
    ethernet_t ethernet;
    ipv4_t ipv4;
    udp_t udp;
    packet_type_t Type;
    padding_len_t paddingLength;
    padding_t padding;
    aggregation_t aggregation;
    msg_length_t Length;
    msg_t[11] Msg;
}

/*
**********************
Các cấu trúc metadata
**********************
*/

// dùng chung cho cả resubmit vì BMv2 không cho truyền giá trị giữa các metadata
// trong deparser, nơi duy nhất cả metadata chính và metadata resubmit có thể được sử dụng
struct metadata_t {
    pool_size_t enqueue_pos;
    pool_size_t dequeue_pos;
}

// placeholder, dành cho các metadata chưa/không cần thiết trong dự án này
struct empty_metadata_t {

}