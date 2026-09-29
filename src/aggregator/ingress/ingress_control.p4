control sw_ingress_control (
    inout hdr_structures_t hdr, inout metadata_t meta, 
    in    psa_ingress_input_metadata_t  std_ingress_input_meta,
    inout psa_ingress_output_metadata_t std_ingress_output_meta
)

{
    /*
    **************************************************************
    Cấu trúc dữ liệu mô phỏng bộ lưu trữ dạng trụ vòng của ingress
    12 Register Array tương ứng với 12 khối của payload gốc, mỗi khối là 4 byte.
    Độ dài các mảng phải bằng nhau vì mỗi gói tin được chia vào 12 mảng Register
    và lưu tại cùng một chỉ số phần tử.
    **************************************************************
    */

    // các pool lưu nội dung các gói tin UDP nhỏ đi vào
    Register<chunk_t, pool_size_t>(MAX_DATA_REG_ARR_SIZES) pool_0;
    Register<chunk_t, pool_size_t>(MAX_DATA_REG_ARR_SIZES) pool_1;
    Register<chunk_t, pool_size_t>(MAX_DATA_REG_ARR_SIZES) pool_2;
    Register<chunk_t, pool_size_t>(MAX_DATA_REG_ARR_SIZES) pool_3;
    Register<chunk_t, pool_size_t>(MAX_DATA_REG_ARR_SIZES) pool_4;
    Register<chunk_t, pool_size_t>(MAX_DATA_REG_ARR_SIZES) pool_5;
    Register<chunk_t, pool_size_t>(MAX_DATA_REG_ARR_SIZES) pool_6;
    Register<chunk_t, pool_size_t>(MAX_DATA_REG_ARR_SIZES) pool_7;
    Register<chunk_t, pool_size_t>(MAX_DATA_REG_ARR_SIZES) pool_8;
    Register<chunk_t, pool_size_t>(MAX_DATA_REG_ARR_SIZES) pool_9;
    Register<chunk_t, pool_size_t>(MAX_DATA_REG_ARR_SIZES) pool_10;
    Register<chunk_t, pool_size_t>(MAX_DATA_REG_ARR_SIZES) pool_11;

    Register<bitmap_t, pool_size_t>(MAX_DATA_REG_ARR_SIZES) occupancy_bitmaps;
    Register<pool_count_t, pool_size_t>(MAX_DATA_REG_ARR_SIZES) available_pools;

    Register<pool_size_t, bit<1>>(1) pool_save_pos;
    Register<saved_size_t, bit<1>>(1) byte_saved_total;

    // danh sách thông tin về phần dữ liệu đã lưu từ các gói tin UDP nhỏ đi vào, mỗi phần dữ liệu có độ dài khác nhau
    // bản thân phần dữ liệu không lưu ở đây, mà trong các pool ở trên
    Register<pool_size_t, list_size_t>(MAX_PKTS_STORED) pkt_data_indices;
    Register<bit<1>, list_size_t>(MAX_PKTS_STORED) pkt_occupied;
    Register<pool_count_t, list_size_t>(MAX_PKTS_STORED) pool_usage_counts;
    Register<bit<8>, list_size_t>(MAX_PKTS_STORED) pkt_data_sizes;
    Register<bitmap_t, list_size_t>(MAX_PKTS_STORED) pkt_column_bitmaps;

    Register<list_size_t, bit<1>>(1) pkt_save_pos;
    Register<list_size_t, bit<1>>(1) pkt_read_pos;
    Register<bit<10>, bit<1>>(1) worker_packet_count;


    action get_operation_bitmap(bit<12> operation_bitmap) {
        meta.operation_bitmap = operation_bitmap;
    }

    table lookup {
        key = {
            meta.occupancy_bitmap: exact;
            meta.no_of_pools: exact;
        }
        size = 24578;
        actions = {
            get_operation_bitmap;
            NoAction;
        }
        default_action = NoAction();
    }

    // pool 0

    action save_pool_0() {
        pool_0.write(meta.pool_save_pos, hdr.Msg[meta.stack_front].msg);
        meta.stack_front = meta.stack_front + 1;
    }

    action read_pool_0() {
        hdr.Msg[0].setValid();
        hdr.Msg[0].msg = pool_0.read(meta.pool_read_pos);
    }

    table ops_pool_0 {
        key = {
            meta.is_aggregation: exact;
            meta.pool_bitmap: exact;
        }
        size = 2;
        actions = {
            save_pool_0;
            read_pool_0;
            NoAction;
        }
        default_action = NoAction();
    }

    // pool 1

    action save_pool_1() {
        pool_1.write(meta.pool_save_pos, hdr.Msg[meta.stack_front].msg);
        meta.stack_front = meta.stack_front + 1;
    }

    action read_pool_1() {
        hdr.Msg[1].setValid();
        hdr.Msg[1].msg = pool_1.read(meta.pool_read_pos);
    }

    table ops_pool_1 {
        key = {
            meta.is_aggregation: exact;
            meta.pool_bitmap: exact;
        }
        size = 2;
        actions = {
            save_pool_1;
            read_pool_1;
            NoAction;
        }
        default_action = NoAction();
    }

    // pool 2

    action save_pool_2() {
        pool_2.write(meta.pool_save_pos, hdr.Msg[meta.stack_front].msg);
        meta.stack_front = meta.stack_front + 1;
    }

    action read_pool_2() {
        hdr.Msg[2].setValid();
        hdr.Msg[2].msg = pool_2.read(meta.pool_read_pos);
    }

    table ops_pool_2 {
        key = {
            meta.is_aggregation: exact;
            meta.pool_bitmap: exact;
        }
        size = 2;
        actions = {
            save_pool_2;
            read_pool_2;
            NoAction;
        }
        default_action = NoAction();
    }

    // pool 3

    action save_pool_3() {
        pool_3.write(meta.pool_save_pos, hdr.Msg[meta.stack_front].msg);
        meta.stack_front = meta.stack_front + 1;
    }

    action read_pool_3() {
        hdr.Msg[3].setValid();
        hdr.Msg[3].msg = pool_3.read(meta.pool_read_pos);
    }

    table ops_pool_3 {
        key = {
            meta.is_aggregation: exact;
            meta.pool_bitmap: exact;
        }
        size = 2;
        actions = {
            save_pool_3;
            read_pool_3;
            NoAction;
        }
        default_action = NoAction();
    }

    // pool 4

    action save_pool_4() {
        pool_4.write(meta.pool_save_pos, hdr.Msg[meta.stack_front].msg);
        meta.stack_front = meta.stack_front + 1;
    }

    action read_pool_4() {
        hdr.Msg[4].setValid();
        hdr.Msg[4].msg = pool_4.read(meta.pool_read_pos);
    }

    table ops_pool_4 {
        key = {
            meta.is_aggregation: exact;
            meta.pool_bitmap: exact;
        }
        size = 2;
        actions = {
            save_pool_4;
            read_pool_4;
            NoAction;
        }
        default_action = NoAction();
    }

    // pool 5

    action save_pool_5() {
        pool_5.write(meta.pool_save_pos, hdr.Msg[meta.stack_front].msg);
        meta.stack_front = meta.stack_front + 1;
    }

    action read_pool_5() {
        hdr.Msg[5].setValid();
        hdr.Msg[5].msg = pool_5.read(meta.pool_read_pos);
    }

    table ops_pool_5 {
        key = {
            meta.is_aggregation: exact;
            meta.pool_bitmap: exact;
        }
        size = 2;
        actions = {
            save_pool_5;
            read_pool_5;
            NoAction;
        }
        default_action = NoAction();
    }

    // pool 6

    action save_pool_6() {
        pool_6.write(meta.pool_save_pos, hdr.Msg[meta.stack_front].msg);
        meta.stack_front = meta.stack_front + 1;
    }

    action read_pool_6() {
        hdr.Msg[6].setValid();
        hdr.Msg[6].msg = pool_6.read(meta.pool_read_pos);
    }

    table ops_pool_6 {
        key = {
            meta.is_aggregation: exact;
            meta.pool_bitmap: exact;
        }
        size = 2;
        actions = {
            save_pool_6;
            read_pool_6;
            NoAction;
        }
        default_action = NoAction();
    }

    // pool 7

    action save_pool_7() {
        pool_7.write(meta.pool_save_pos, hdr.Msg[meta.stack_front].msg);
        meta.stack_front = meta.stack_front + 1;
    }

    action read_pool_7() {
        hdr.Msg[7].setValid();
        hdr.Msg[7].msg = pool_7.read(meta.pool_read_pos);
    }

    table ops_pool_7 {
        key = {
            meta.is_aggregation: exact;
            meta.pool_bitmap: exact;
        }
        size = 2;
        actions = {
            save_pool_7;
            read_pool_7;
            NoAction;
        }
        default_action = NoAction();
    }

    // pool 8

    action save_pool_8() {
        pool_8.write(meta.pool_save_pos, hdr.Msg[meta.stack_front].msg);
        meta.stack_front = meta.stack_front + 1;
    }

    action read_pool_8() {
        hdr.Msg[8].setValid();
        hdr.Msg[8].msg = pool_8.read(meta.pool_read_pos);
    }

    table ops_pool_8 {
        key = {
            meta.is_aggregation: exact;
            meta.pool_bitmap: exact;
        }
        size = 2;
        actions = {
            save_pool_8;
            read_pool_8;
            NoAction;
        }
        default_action = NoAction();
    }

    // pool 9

    action save_pool_9() {
        pool_9.write(meta.pool_save_pos, hdr.Msg[meta.stack_front].msg);
        meta.stack_front = meta.stack_front + 1;
    }

    action read_pool_9() {
        hdr.Msg[9].setValid();
        hdr.Msg[9].msg = pool_9.read(meta.pool_read_pos);
    }

    table ops_pool_9 {
        key = {
            meta.is_aggregation: exact;
            meta.pool_bitmap: exact;
        }
        size = 2;
        actions = {
            save_pool_9;
            read_pool_9;
            NoAction;
        }
        default_action = NoAction();
    }

    // pool 10

    action save_pool_10() {
        pool_10.write(meta.pool_save_pos, hdr.Msg[meta.stack_front].msg);
        meta.stack_front = meta.stack_front + 1;
    }

    action read_pool_10() {
        hdr.Msg[10].setValid();
        hdr.Msg[10].msg = pool_10.read(meta.pool_read_pos);
    }

    table ops_pool_10 {
        key = {
            meta.is_aggregation: exact;
            meta.pool_bitmap: exact;
        }
        size = 2;
        actions = {
            save_pool_10;
            read_pool_10;
            NoAction;
        }
        default_action = NoAction();
    }

    // pool 11

    action save_pool_11() {
        pool_11.write(meta.pool_save_pos, hdr.Msg[meta.stack_front].msg);
        meta.stack_front = meta.stack_front + 1;
    }

    action read_pool_11() {
        hdr.Msg[11].setValid();
        hdr.Msg[11].msg = pool_11.read(meta.pool_read_pos);
    }

    table ops_pool_11 {
        key = {
            meta.is_aggregation: exact;
            meta.pool_bitmap: exact;
        }
        size = 2;
        actions = {
            save_pool_11;
            read_pool_11;
            NoAction;
        }
        default_action = NoAction();
    }

    // Apending the remaining bytes to the last message in the stack

    action append_stack_idx_1() {
        hdr.Msg[0].setValid();
        hdr.Msg[0].msg = meta.remaining_msg;
    }

    action append_stack_idx_2() {
        hdr.Msg[1].setValid();
        hdr.Msg[1].msg = meta.remaining_msg;
    }

    action append_stack_idx_3() {
        hdr.Msg[2].setValid();
        hdr.Msg[2].msg = meta.remaining_msg;
    }

    action append_stack_idx_4() {
        hdr.Msg[3].setValid();
        hdr.Msg[3].msg = meta.remaining_msg;
    }

    action append_stack_idx_5() {
        hdr.Msg[4].setValid();
        hdr.Msg[4].msg = meta.remaining_msg;
    }

    action append_stack_idx_6() {
        hdr.Msg[5].setValid();
        hdr.Msg[5].msg = meta.remaining_msg;
    }

    action append_stack_idx_7() {
        hdr.Msg[6].setValid();
        hdr.Msg[6].msg = meta.remaining_msg;
    }

    action append_stack_idx_8() {
        hdr.Msg[7].setValid();
        hdr.Msg[7].msg = meta.remaining_msg;
    }

    action append_stack_idx_9() {
        hdr.Msg[8].setValid();
        hdr.Msg[8].msg = meta.remaining_msg;
    }

    action append_stack_idx_10() {
        hdr.Msg[9].setValid();
        hdr.Msg[9].msg = meta.remaining_msg;
    }

    action append_stack_idx_11() {
        hdr.Msg[10].setValid();
        hdr.Msg[10].msg = meta.remaining_msg;
    }

    action append_stack_idx_12() {
        hdr.Msg[11].setValid();
        hdr.Msg[11].msg = meta.remaining_msg;
    }

    table append_stack {
        key = {
            meta.no_of_pools: exact;
        }
        size = 12;
        actions = {
            append_stack_idx_1;
            append_stack_idx_2;
            append_stack_idx_3;
            append_stack_idx_4;
            append_stack_idx_5;
            append_stack_idx_6;
            append_stack_idx_7;
            append_stack_idx_8;
            append_stack_idx_9;
            append_stack_idx_10;
            append_stack_idx_11;
            append_stack_idx_12;
            NoAction;
        }
        default_action = NoAction();
    }

    apply {
        // đọc tổng số byte đã lưu từ nội dung các gói tin UDP nhỏ đi vào
        saved_size_t saved_total = byte_saved_total.read(0);
        bit<10> wrkr_pkt_count = worker_packet_count.read(0);
        
        // luồng làm việc nếu không phải gói tin làm việc tổng hợp
        if (meta.is_aggregation == 0)
        {
            // Nếu không phải gói UDP hoặc gói UDP dài hơn mức có thể lưu,
            // chuyển tiếp như bình thường
            if (hdr.udp.length >= 56 || !hdr.udp.isValid()) 
            {
                send_to_port(std_ingress_output_meta, (PortId_t)2);
                return;
            }

            // Lấy vị trí trống đầu tiên trong danh sách lưu thông tin về
            // các gói UDP nhỏ đi vào, danh sách này không thật sự chứa nội dung.
            meta.list_save_pos = pkt_save_pos.read(0);

            // Đọc trạng thái chiếm dụng tại vị trí đã lấy.
            bit<1> list_slot_occupied = pkt_occupied.read(meta.list_save_pos);

            // Vì vị trí trống sẽ dịch về sau 1 phần tử với mỗi lần ghi,
            // việc vị trí không còn trống nghĩa là danh sách đã đầy.
            // Bỏ qua bước lưu nội dung và tổng hơp cũng như chuyển thẳng
            // đến bước chuyển tiếp như một gói tin bình thường.
            if (list_slot_occupied == 1)
            {
                send_to_port(std_ingress_output_meta, (PortId_t)2);
                return;
            }

            // Lấy vị trí đầu tiên trống hoàn toàn trong cấu trúc các pool
            // lưu nội dung của các gói UDP nhỏ đi vào.
            // Trước khi lưu nội dung vào vị trí này, cần kiểm tra hai vị trí liền
            // trước nó xem vẫn còn đủ số pool trống để lưu dữ liệu vào hay không.
            meta.pool_save_pos = pool_save_pos.read(0) - 2;
            meta.col_rem_pools = available_pools.read(meta.pool_save_pos);

            if (meta.col_rem_pools < meta.no_of_pools)
            {
                meta.pool_save_pos = meta.pool_save_pos + 1; // -1
                meta.col_rem_pools = available_pools.read(meta.pool_save_pos);
                if (meta.col_rem_pools < meta.no_of_pools)
                {
                    // Nếu hai vị trí liền trước đều không đủ, kiểm tra vị trí hiện tại
                    // (vị trí đầu tiên trống hoàn toàn)
                    meta.pool_save_pos = meta.pool_save_pos + 1; // 0 (pool_save_pos[0])
                    meta.col_rem_pools = available_pools.read(meta.pool_save_pos);
                    if (meta.col_rem_pools < meta.no_of_pools)
                    {
                        // Nếu vị trí đáng lẽ phải là vị trí đầu tiên trống hoàn toàn cũng
                        // không đủ, thì danh sách các pool đã đầy, và con trỏ đã đi hết
                        // một vòng. Để tránh bỏ lỡ các khoảng trống có thể dùng được,
                        // có thểkiểm tra thêm một cột tiếp theo
                        meta.pool_save_pos = meta.pool_save_pos + 1; // +1
                        meta.col_rem_pools = available_pools.read(meta.pool_save_pos);
                        // Nếu cột tiếp theo cũng không đủ khoảng trống, bỏ qua
                        // việc lưu nội dung gói tin cho tổng hợp và chuyển tiếp
                        // như gói tin bình thường nhằm tránh lãng phí thời gian
                        // và tài nguyên tính toán của switch.
                        if (meta.col_rem_pools < meta.no_of_pools)
                        {
                            send_to_port(std_ingress_output_meta, (PortId_t)2);
                            return;
                        }
                        meta.move_pool_save_pos = true;
                    }
                }
            }
            
            // đọc chuỗi bitmap chiếm dụng của cột pool tại vị trí đã lấy, để tính toán
            // các pool nào sẽ được lưu nội dung gói tin nhỏ đi vào và các pool
            meta.occupancy_bitmap = occupancy_bitmaps.read(meta.pool_save_pos);

            // sau khi áp dụng bảng, chuỗi bitmap meta.operation_bitmap sẽ chứa các pool được chọn để lưu nội dung gói tin nhỏ đi vào
            if (lookup.apply().miss) {
                send_to_port(std_ingress_output_meta, (PortId_t)2);
                return;
            }

            // Thêm các byte còn lại (không chia hết cho 4) vào phần tử cuối
            // của header stack hdr.Msg[]
            if (meta.rem_bytes_count > 0)
            {
                append_stack.apply();
            }

            // đẩy con trỏ vị trí trống đầu tiên trong danh sách các gói UDP nhỏ đi vào về sau 1 phần tử
            pkt_save_pos.write(0, meta.list_save_pos + 1);
            // đánh dấu vị trí vừa lấy là đã chiếm dụng
            pkt_occupied.write(meta.list_save_pos, 1);

            // lưu lại các thông tin về nội dung gói tin nhỏ, gồm:
            // chỉ số trong cấu trúc các pool
            pkt_data_indices.write(meta.list_save_pos, meta.pool_save_pos);
            // độ dài thật của nội dung
            pkt_data_sizes.write(meta.list_save_pos, (bit<8>)(hdr.udp.length - 8));
            // số pool chiếm dụng trong cột, dùng để tính toán trừ ra khỏi số pool
            // bị chiếm dụng tại cột khi gói làm việc tổng hợp lấy phần nội dung gói nhỏ
            // được lưu tại cột.
            pool_usage_counts.write(meta.list_save_pos, meta.no_of_pools);

            // Lưu chuỗi bitmap này vào danh sách bitmap của các gói UDP nhỏ đi vào
            // gói làm việc tổng hợp sẽ đọc chuỗi này để biết các pool cần đọc để lấy nội dung gói tin nhỏ đã vào trước đó
            pkt_column_bitmaps.write(meta.list_save_pos, meta.operation_bitmap);

            // Dùng phép | (OR trên từng cặp bit của hai chuỗi bit) để đánh dấu các pool sắp được ghi vào là bị chiếm dụng.
            // Phép | sẽ giữ nguyên các bit 1 trong chuỗi bitmap chiếm dụng hiện tại
            // (giá trị 1 trong occupancy_bitmap và 0 trong operation_bitmap), và ghi các bit 1 trong chuỗi operation_bitmap
            // vào vị trí tương ứng trong occupancy_bitmap (trước khi ghi đang là 0).
            meta.occupancy_bitmap = meta.occupancy_bitmap | meta.operation_bitmap;
            // occupancy_bitmaps.write(
            //     meta.pool_save_pos, meta.occupancy_bitmap
            // );

            available_pools.write(meta.pool_save_pos, meta.col_rem_pools - meta.no_of_pools);

            // cộng độ dài nội dung gói tin sắp được lưu vào tổng số byte nội dung đã lưu từ các gói tin UDP nhỏ đi vào
            saved_total = saved_total + (saved_size_t)(hdr.udp.length - 8);
            byte_saved_total.write(0, saved_total);

            // Nếu cột chuẩn bị được ghi trong pool đang trống hoàn toàn,
            // đẩy giá trị con trỏ vị trí trống đầu tiên lên một phần tử.
            if (meta.move_pool_save_pos == true)
            {
                pool_save_pos.write(0, meta.pool_save_pos);
            }
            meta.stack_front = 0;
        }
        // luồng làm việc nếu là gói tin làm việc tổng hợp
        else
        {
            // Chỉ cộng thêm 1 nếu đây là gói tin đươc gửi từ control plane hoặc nguồn khác,
            // không phải gói tin đã được recirculate trong pipeline.
            if (std_ingress_input_meta.packet_path != PSA_PacketPath_t.RECIRCULATE)
            {
                wrkr_pkt_count = wrkr_pkt_count + 1;
            }
            
            if (wrkr_pkt_count > MAX_NUMBER_OF_WORKER_PACKETS)
            {
                ingress_drop(std_ingress_output_meta);
                return;
            }

            worker_packet_count.write(0, wrkr_pkt_count);

            if (saved_total == 0)
            {
                if (hdr.aggregation.num == 0)
                {
                    ingress_drop(std_ingress_output_meta);
                }
                else {
                    send_to_port(std_ingress_output_meta, (PortId_t)2);
                    // hdr.aggregation.num khác 0 khi và chỉ khi gói tin đã được recirculate ít nhất 2 lần.
                    // Do đó, điều kiện std_ingress_input_meta.packet_path == PSA_PacketPath_t.RECIRCULATE sẽ luôn đúng
                    // trước khi tới được khối mã này.
                    // Vì vậy không cần lo ngại việc wrkr_pkt_count bị trừ đi 2 lần.
                }
                worker_packet_count.write(0, wrkr_pkt_count - 1);
                return;
            }

            // Lấy vị trí đầu tiên có nội dung gói tin nhỏ đã lưu trong danh sách
            meta.list_read_pos = pkt_read_pos.read(0);
            
            // Đọc các thông tin về nội dung gói tin nhỏ đã lưu từ danh sách, bao gồm:
            // Chỉ số cột các pool lưu nội dung gói tin nhỏ đã lưu
            meta.pool_read_pos = pkt_data_indices.read(meta.list_read_pos);
            // Số pool phần nội dung này chiếm trong cột
            meta.no_of_pools = pool_usage_counts.read(meta.list_read_pos);
            // Bitmap thể hiện các pool nào trong cột là danh cho đoạn nội dung
            // đang xét
            meta.operation_bitmap = pkt_column_bitmaps.read(meta.list_read_pos);
            // Độ dài thật của nội dung gói tin nhỏ đã lưu
            // (với các đoạn nội dung có độ dài không chia hết cho 4, sẽ có 1, 2, hoặc 3 byte toàn 0 ở cuối)
            meta.read_payload_size = (saved_size_t)(pkt_data_sizes.read(meta.list_read_pos));
            
            // Đọc số pool còn lại trong cột, số này sẽ được cộng thêm số pool
            // vừa được giải phóng khi gói làm việc tổng hợp lấy nội dung
            // gói tin nhỏ đã lưu.
            meta.col_rem_pools = available_pools.read(meta.pool_read_pos);
        }
        
        meta.pool_bitmap = (bitmap_t)meta.operation_bitmap[0:0];
        ops_pool_0.apply();
        meta.pool_bitmap = (bitmap_t)meta.operation_bitmap[1:1];
        ops_pool_1.apply();
        meta.pool_bitmap = (bitmap_t)meta.operation_bitmap[2:2];
        ops_pool_2.apply();
        meta.pool_bitmap = (bitmap_t)meta.operation_bitmap[3:3];
        ops_pool_3.apply();
        meta.pool_bitmap = (bitmap_t)meta.operation_bitmap[4:4];
        ops_pool_4.apply();
        meta.pool_bitmap = (bitmap_t)meta.operation_bitmap[5:5];
        ops_pool_5.apply();
        meta.pool_bitmap = (bitmap_t)meta.operation_bitmap[6:6];
        ops_pool_6.apply();
        meta.pool_bitmap = (bitmap_t)meta.operation_bitmap[7:7];
        ops_pool_7.apply();
        meta.pool_bitmap = (bitmap_t)meta.operation_bitmap[8:8];
        ops_pool_8.apply();
        meta.pool_bitmap = (bitmap_t)meta.operation_bitmap[9:9];
        ops_pool_9.apply();
        meta.pool_bitmap = (bitmap_t)meta.operation_bitmap[10:10];
        ops_pool_10.apply();
        meta.pool_bitmap = (bitmap_t)meta.operation_bitmap[11:11];
        ops_pool_11.apply();
        
        occupancy_bitmaps.write(meta.pool_save_pos, meta.occupancy_bitmap);

        if (meta.is_aggregation == 0)
        {
            // Nếu có ít nhất 1466 bytes dữ liệu được lưu trữ (đủ để tạo thành nội dung tổng hợp mới)
            // và chưa có gói tin làm việc tổng hợp nào đang hoạt động, chuyển gói này thành gói tổng hợp và recirc
            if (saved_total >= 1024 && wrkr_pkt_count < MAX_NUMBER_OF_WORKER_PACKETS)
            {
                // Hủy các trường header liên quan tới gói tin nhỏ
                hdr.Length.setInvalid();
                hdr.Msg[0].setInvalid();
                hdr.Msg[1].setInvalid();
                hdr.Msg[2].setInvalid();
                hdr.Msg[3].setInvalid();
                hdr.Msg[4].setInvalid();
                hdr.Msg[5].setInvalid();
                hdr.Msg[6].setInvalid();
                hdr.Msg[7].setInvalid();
                hdr.Msg[8].setInvalid();
                hdr.Msg[9].setInvalid();
                hdr.Msg[10].setInvalid();
                hdr.Msg[11].setInvalid();
                hdr.RemainingByte.setInvalid();
                hdr.RemainingTwoBytes.setInvalid();
                hdr.RemainingThreeBytes.setInvalid();

                // Thêm và thiết lập các trường header liên quan tới gói tin tổng hợp
                hdr.udp.length = 14;
                hdr.ipv4.totalLen = hdr.udp.length + 20;
                hdr.Type.setValid();
                hdr.Type.type_field = 0xFFFB;
                hdr.aggregation.setValid();
                hdr.aggregation.num = 0;
                hdr.aggregation.len = 0;

                // Gửi đến cổng recirc/loopback để gói tin được xử lý lại trong pipeline, lần này là gói tổng hợp
                send_to_port(std_ingress_output_meta, PSA_PORT_RECIRCULATE);
                worker_packet_count.write(0, wrkr_pkt_count + 1);
                return;
            }
            // Nếu không đạt điều kiện, drop vì nội dung đã được lưu và header không cần sử dụng nữa.
            ingress_drop(std_ingress_output_meta);
        }
        else {
            // Đọc chuỗi bitmap chiếm dụng của cột pool tại vị trí đã lấy.
            // Các bit đại diện cho các pool vừa đươc giải phóng sẽ được
            // đặt giá trị từ 1 về lại 0.
            meta.occupancy_bitmap = occupancy_bitmaps.read(meta.pool_read_pos);

            // Dùng phép XOR, các cặp bit tương ứng có giá trị 1
            // trong cả 2 chuỗi operation_bitmap và occupancy_bitmap,
            // qua phép XOR, sẽ trả về 0.
            meta.occupancy_bitmap = meta.occupancy_bitmap ^ meta.operation_bitmap;
            // Ghi lại vào register array giá trị mới tại phần tử đang xét
            occupancy_bitmaps.write(meta.pool_read_pos, meta.occupancy_bitmap);
            // Cộng số pool vừa được giải phóng vào số pool còn lại trong cột
            meta.col_rem_pools = meta.col_rem_pools + meta.no_of_pools;
            // Ghi lại giá trị mới vào register array tại phần tử đang xét
            available_pools.write(meta.pool_read_pos, meta.col_rem_pools);

            // Ghi giá trị 0 vào vị trí đã đọc trong danh sách,
            // đánh dấu vị trí này là trống, có thể lưu thông tin gói mới vào đấy.
            pkt_occupied.write(meta.list_read_pos, 0);
            // Cập nhật vị trí đọc tiếp theo trong danh sách
            pkt_read_pos.write(0, meta.list_read_pos + 1);

            // Giảm tổng số byte đã lưu một khoảng bằng
            // độ dài nội dung gói tin nhỏ vừa được lấy ra.
            saved_total = saved_total - meta.read_payload_size;
            byte_saved_total.write(0, saved_total);

            // Thêm một trường len đại diện cho độ dài nội dung gói tin nhỏ vừa được lấy ra vào header tổng hợp.
            hdr.Length.setValid();
            // Gán dữ liệu cho trường vừa thêm
            hdr.Length.len = (bit<8>)meta.read_payload_size;
            // Tăng số đoạn nội dung gói nhỏ đã ghép vào gói tổng hợp lên 1
            hdr.aggregation.num = hdr.aggregation.num + 1;
            // Tăng độ dài nội dung gói tổng hợp lên bằng độ dài nội dung gói nhỏ vừa được lấy ra
            // (đây là độ dài thực, không tính các byte 0 thêm vào cuối để chia hết cho 4)
            hdr.aggregation.len = hdr.aggregation.len + (bit<16>)meta.read_payload_size;
            // Tăng độ dài gói UDP lên một khoảng bằng 4 lần số pool vừa được lấy ra (mỗi pool là 4 byte).
            // Lý do dùng hai cách tính khác nhau là để dễ kiểm tra tính hiệu quả của quá trình tổng hợp
            // ở khía cạnh dữ liệu (số byte nội dung thực tế, số byte 0 được đệm vào).
            hdr.udp.length = hdr.udp.length + 4 * (bit<16>)meta.no_of_pools + 1;
            hdr.ipv4.totalLen = hdr.udp.length + 20;
            
            if (hdr.udp.length > 1426)
            {
                worker_packet_count.write(0, wrkr_pkt_count - 1);
                send_to_port(std_ingress_output_meta, (PortId_t)2);
            }
            else {
                send_to_port(std_ingress_output_meta, PSA_PORT_RECIRCULATE);
            }
        }
    }
}
