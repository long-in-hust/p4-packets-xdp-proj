parser sw_ingress_parser (
    packet_in packet, out hdr_structures_t hdr, 
    inout metadata_t meta,
    in psa_ingress_parser_input_metadata_t std_parser_meta,
    in metadata_t resubmit_meta,
    in empty_metadata_t recirculate_meta
)

{
    state start {
        transition parse_ethernet;
    }

    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select (hdr.ethernet.etherType) {
            0x0800: parse_ipv4;
            default: accept;
        }
    }

    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        transition select (hdr.ipv4.protocol) {
            17: parse_udp;
            default: accept;
        }
    }

    state parse_udp {
        packet.extract(hdr.udp);
        transition parse_type;
    }

    state parse_type {
        meta.tmp_msg_type = packet.lookahead<packet_type_t>().type_field;
        transition select (meta.tmp_msg_type) {
            0xfffb: parse_aggregation_h;
            default: get_len;
        }
    }

    state get_len {
        meta.tmp_msg_len = ((hdr.udp.length - 8) / 4);
        transition select (meta.tmp_msg_len) {
            0: get_remaining_bytes;
            1: msg1;
            2: msg2;
            3: msg3;
            4: msg4;
            5: msg5;
            6: msg6;
            7: msg7;
            8: msg8;
            9: msg9;
            10: msg10;
            11: msg11;
            default: accept;
        }
    }

    state msg1 {
        meta.no_of_pools = 1;
        packet.extract(hdr.Msg[0]);
        transition get_remaining_bytes;
    }

    state msg2 {
        meta.no_of_pools = 2;
        packet.extract(hdr.Msg[0]);
        packet.extract(hdr.Msg[1]);
        transition get_remaining_bytes;
    }

    state msg3 {
        meta.no_of_pools = 3;
        packet.extract(hdr.Msg[0]);
        packet.extract(hdr.Msg[1]);
        packet.extract(hdr.Msg[2]);
        transition get_remaining_bytes;
    }

    state msg4 {
        meta.no_of_pools = 4;
        packet.extract(hdr.Msg[0]);
        packet.extract(hdr.Msg[1]);
        packet.extract(hdr.Msg[2]);
        packet.extract(hdr.Msg[3]);
        transition get_remaining_bytes;
    }

    state msg5 {
        meta.no_of_pools = 5;
        packet.extract(hdr.Msg[0]);
        packet.extract(hdr.Msg[1]);
        packet.extract(hdr.Msg[2]);
        packet.extract(hdr.Msg[3]);
        packet.extract(hdr.Msg[4]);
        transition get_remaining_bytes;
    }

    state msg6 {
        meta.no_of_pools = 6;
        packet.extract(hdr.Msg[0]);
        packet.extract(hdr.Msg[1]);
        packet.extract(hdr.Msg[2]);
        packet.extract(hdr.Msg[3]);
        packet.extract(hdr.Msg[4]);
        packet.extract(hdr.Msg[5]);
        transition get_remaining_bytes;
    }

    state msg7 {
        meta.no_of_pools = 7;
        packet.extract(hdr.Msg[0]);
        packet.extract(hdr.Msg[1]);
        packet.extract(hdr.Msg[2]);
        packet.extract(hdr.Msg[3]);
        packet.extract(hdr.Msg[4]);
        packet.extract(hdr.Msg[5]);
        packet.extract(hdr.Msg[6]);
        transition get_remaining_bytes;
    }

    state msg8 {
        meta.no_of_pools = 8;
        packet.extract(hdr.Msg[0]);
        packet.extract(hdr.Msg[1]);
        packet.extract(hdr.Msg[2]);
        packet.extract(hdr.Msg[3]);
        packet.extract(hdr.Msg[4]);
        packet.extract(hdr.Msg[5]);
        packet.extract(hdr.Msg[6]);
        packet.extract(hdr.Msg[7]);
        transition get_remaining_bytes;
    }

    state msg9 {
        meta.no_of_pools = 9;
        packet.extract(hdr.Msg[0]);
        packet.extract(hdr.Msg[1]);
        packet.extract(hdr.Msg[2]);
        packet.extract(hdr.Msg[3]);
        packet.extract(hdr.Msg[4]);
        packet.extract(hdr.Msg[5]);
        packet.extract(hdr.Msg[6]);
        packet.extract(hdr.Msg[7]);
        packet.extract(hdr.Msg[8]);
        transition get_remaining_bytes;
    }

    state msg10 {
        meta.no_of_pools = 10;
        packet.extract(hdr.Msg[0]);
        packet.extract(hdr.Msg[1]);
        packet.extract(hdr.Msg[2]);
        packet.extract(hdr.Msg[3]);
        packet.extract(hdr.Msg[4]);
        packet.extract(hdr.Msg[5]);
        packet.extract(hdr.Msg[6]);
        packet.extract(hdr.Msg[7]);
        packet.extract(hdr.Msg[8]);
        packet.extract(hdr.Msg[9]);
        transition get_remaining_bytes;
    }

    state msg11 {
        meta.no_of_pools = 11;
        packet.extract(hdr.Msg[0]);
        packet.extract(hdr.Msg[1]);
        packet.extract(hdr.Msg[2]);
        packet.extract(hdr.Msg[3]);
        packet.extract(hdr.Msg[4]);
        packet.extract(hdr.Msg[5]);
        packet.extract(hdr.Msg[6]);
        packet.extract(hdr.Msg[7]);
        packet.extract(hdr.Msg[8]);
        packet.extract(hdr.Msg[9]);
        packet.extract(hdr.Msg[10]);
        transition get_remaining_bytes;
    }

    state parse_aggregation_h {
        packet.extract(hdr.Type);
        packet.extract(hdr.aggregation);
        meta.is_aggregation = 1;
        transition accept;
    }

    state get_remaining_bytes {
        meta.rem_bytes_count = (bit<8>)((hdr.udp.length - 8) % 4);
        transition select (meta.rem_bytes_count) {
            1: parse_remaining_byte1;
            2: parse_remaining_byte2;
            3: parse_remaining_byte3;
            default: accept;
        }
    }

    state parse_remaining_byte1 {
        meta.no_of_pools = meta.no_of_pools + 1;
        packet.extract(hdr.RemainingByte);
        meta.remaining_msg[31:24] = hdr.RemainingByte.byte;
        transition accept;
    }


    state parse_remaining_byte2 {
        meta.no_of_pools = meta.no_of_pools + 1;
        packet.extract(hdr.RemainingTwoBytes);
        meta.remaining_msg[31:16] = hdr.RemainingTwoBytes.bytes;
        transition accept;
    }

    state parse_remaining_byte3 {
        meta.no_of_pools = meta.no_of_pools + 1;
        packet.extract(hdr.RemainingThreeBytes);
        meta.remaining_msg[31:8] = hdr.RemainingThreeBytes.bytes;
        transition accept;
    }
}