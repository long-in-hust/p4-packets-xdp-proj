control sw_ingress_deparser (
    packet_out packet,
    out empty_metadata_t clone_i2e_meta,
    out metadata_t resubmit_meta,
    out empty_metadata_t normal_meta,
    inout hdr_structures_t hdr,
    in metadata_t meta,
    in psa_ingress_output_metadata_t std_deparser_meta
)

{
    InternetChecksum() checksum;

    apply 
    {
        // tính lại checksum IPv4
        checksum.clear();
        checksum.add({
            /* 16-bit word  0   */ hdr.ipv4.version, hdr.ipv4.ihl, hdr.ipv4.diffserv,
            /* 16-bit word  1   */ hdr.ipv4.totalLen,
            /* 16-bit word  2   */ hdr.ipv4.identification,
            /* 16-bit word  3   */ hdr.ipv4.flags, hdr.ipv4.fragOffset,
            /* 16-bit word  4   */ hdr.ipv4.ttl, hdr.ipv4.protocol,
            /* 16-bit word  5 skip hdr.ipv4.hdrChecksum, */
            /* 16-bit words 6-7 */ hdr.ipv4.srcAddr,
            /* 16-bit words 8-9 */ hdr.ipv4.dstAddr
        });
        hdr.ipv4.hdrChecksum = checksum.get();

        packet.emit(hdr.ethernet);
        packet.emit(hdr.ipv4);
        packet.emit(hdr.udp);
        packet.emit(hdr.Type);

        packet.emit(hdr.aggregation);
        
        packet.emit(hdr.Length);
        packet.emit(hdr.Msg);
        packet.emit(hdr.RemainingByte);
        packet.emit(hdr.RemainingTwoBytes);
        packet.emit(hdr.RemainingThreeBytes);
    }
}