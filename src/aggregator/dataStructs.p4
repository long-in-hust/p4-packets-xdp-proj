/*
****************************************
Định nghĩa một số kiểu dữ liệu hay dùng
****************************************
*/

typedef bit<32> chunk_t;
typedef bit<6> pool_size_t;
typedef bit<7> list_size_t;
typedef bit<12> saved_size_t;
typedef bit<12> bitmap_t;
typedef bit<4> pool_count_t;

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
    bit<16> type_field;
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

header byte_t {
    bit<8> byte;
}

header two_bytes_t {
    bit<16> bytes;
}

header three_bytes_t {
    bit<24> bytes;
}

struct hdr_structures_t {
    packet_out_t PacketOut;
    ethernet_t ethernet;
    ipv4_t ipv4;
    udp_t udp;
    packet_type_t Type;
    aggregation_t aggregation;
    msg_length_t Length;
    msg_t[12] Msg;
    byte_t RemainingByte;
    two_bytes_t RemainingTwoBytes;
    three_bytes_t RemainingThreeBytes;
}

/*
****************
Một số cấu trúc khác
****************
*/

// struct remaining_bytes_count_t {
//     bit<2> remBytes;
// }

/*
**********************
Các cấu trúc metadata
**********************
*/

// dùng chung cho cả resubmit vì BMv2 không cho truyền giá trị giữa các metadata
// trong deparser, nơi duy nhất cả metadata chính và metadata resubmit có thể được sử dụng
struct metadata_t {
    bit<32> remaining_msg;
    bit<8> rem_bytes_count;

    list_size_t list_save_pos;
    list_size_t list_read_pos;

    pool_size_t pool_save_pos;
    pool_size_t pool_read_pos;
    // bit<8> pool_save_missed_times;
    bool move_pool_save_pos;

    pool_count_t no_of_pools;
    pool_count_t col_rem_pools;

    bit<1> is_aggregation;
    bitmap_t occupancy_bitmap;
    bitmap_t operation_bitmap;
    bitmap_t pool_bitmap;

    saved_size_t read_payload_size;
    bit<4> stack_front;
}

// placeholder, dùng để gán kiểu cho các metadata chưa/không cần thiết trong dự án này
struct empty_metadata_t {

}