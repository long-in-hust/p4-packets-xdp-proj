#include <core.p4>
#include <psa.p4>

#include "macros/macros.p4"
#include "dataStructs.p4"

/* 
------- Switch logic --------
*/

/*
parser sw_ingress_parser (
    packet_in packet, out hdr_structures_t hdr, 
    inout metadata_t meta,
    in psa_ingress_parser_input_metadata_t std_parser_meta,
    in metadata_t resubmit_meta,
    in empty_metadata_t recirculate_meta
)
*/
#include "ingress/ingress_parser.p4"

/*
control sw_ingress_control (
    inout hdr_structures_t hdr, inout metadata_t meta, 
    in    psa_ingress_input_metadata_t  std_ingress_input_meta,
    inout psa_ingress_output_metadata_t std_ingress_output_meta
)
*/
#include "ingress/ingress_control.p4"

/*
control sw_ingress_deparser (
    packet_out packet,
    out empty_metadata_t clone_i2e_meta,
    out metadata_t resubmit_meta,
    out empty_metadata_t normal_meta,
    inout hdr_structures_t hdr,
    in metadata_t meta,
    in psa_ingress_output_metadata_t std_deparser_meta
)
*/
#include "ingress/ingress_deparser.p4"

parser sw_egress_parser(packet_in packet,
        out hdr_structures_t hdr,
        inout metadata_t meta,
        in psa_egress_parser_input_metadata_t std_parser_input_meta,
        in empty_metadata_t normal_meta,
        in empty_metadata_t clone_i2e_meta,
        in empty_metadata_t clone_e2e_meta
    )
{
    state start {
        packet.extract(hdr.ethernet);
        transition accept;
    }
}

control sw_egress_control(inout hdr_structures_t hdr, inout metadata_t meta, 
        in    psa_egress_input_metadata_t  std_egress_input_meta,
        inout psa_egress_output_metadata_t std_egress_output_meta
    )
{
    apply {
        
    }
}

control sw_egress_deparser(packet_out packet,
        out empty_metadata_t clone_e2e_meta,    
        out empty_metadata_t recirculate_meta,
        inout hdr_structures_t hdr,
        in metadata_t meta,
        in psa_egress_output_metadata_t std_deparser_output_meta,
        in psa_egress_deparser_input_metadata_t std_deparser_input_meta
    )
{
    apply {
        packet.emit(hdr.ethernet);
    }
}

IngressPipeline(
    sw_ingress_parser(),
    sw_ingress_control(),
    sw_ingress_deparser()
) main_ingress;

EgressPipeline(
    sw_egress_parser(),
    sw_egress_control(),
    sw_egress_deparser()
) main_egress;

PSA_Switch(
    main_ingress, 
    PacketReplicationEngine(), 
    main_egress, 
    BufferingQueueingEngine()
) main;