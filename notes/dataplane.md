# Giải thích mã nguồn lớp dữ liệu

## Switch tổng hợp:

### Luồng của gói tin:

1. Gói tin vào switch.

2. Switch cấp một buffer dành cho gói tin (PacketBuffer).

    Khoảng buffer này được cấp riêng cho gói. Kích thước bằng kích thước gói + 512 byte. (Gói tin 51 byte, không gian được cấp cho buffer sẽ có kích thước 51 + 512 = 563). Giới hạn buffer bằng gói vào + 512 byte được triển khai tại dòng thứ 245 của file `target/simple_switch/simple_switch.cpp`, trong hàm `SimpleSwitch::receive_`:

    ```cpp
    int
    SimpleSwitch::receive_(port_t port_num, const char *buffer, int len) {
    [...]
        // dòng 245
        auto packet = new_packet_ptr(port_num, packet_id++, len,
                                    bm::PacketBuffer(len + 512, buffer, len));
    [...]
    }
    ```

    Điều này đồng nghĩa với việc gói tin sau khi tổng hợp chỉ được phình ra tối đa 512 byte so với kích thước ban đầu. Nếu gói tin sau khi tổng hợp vượt quá giới hạn này, switch sẽ drop gói tin đó. Đây là hạn chế lớn, vì về lý thuyết, có thể tổng hợp gói tin lên kích thước tối đa là 1518 byte (kích thước tối đa của một gói tin Ethernet).

    Với giới hạn buffer hiện tại, khi nhận một gói tin có kích thước ban đầu là 51 byte, gói tin sau tổng hợp chỉ có thể đạt kích thước tối đa là 563 byte. Một số kiến trúc switch khác như Tofino có thể cấp buffer lớn hơn, do đó có thể tổng hợp gói tin lên gần kích thước MTU (Wang, 2020).

    ```log
    [13:32:39.961390] [bmv2] [T] [thread 56325] Constructor: Initializing packet buffer...
    [13:32:39.961410] [bmv2] [T] [thread 56325] Pushing 51 bytes to packet buffer (data size before push: 0) - Buffer size before push is 563
    [13:32:39.961414] [bmv2] [T] [thread 56325] Data size after push: 51
    ```

    Các PacketBuffer là một phần tử của InputBuffer. Cũng trong phương thức `SimpleSwitch::receive_`, sau khi tạo PacketBuffer, nó sẽ được đẩy vào InputBuffer của switch. Việc này được triển khai tại dòng thứ 271 của file `target/simple_switch/simple_switch.cpp`:

    ```cpp
    // dòng 271
    input_buffer->push_front(
        InputBuffer::PacketType::NORMAL, std::move(packet));
    ```

    Do đó, để can thiệp vào nhiều gói tin, cần lưu các thông tin bên trong chúng vào một kiểu dữ liệu stateful, với V1Model, đó có thể là register hoặc counter.

3. Gói tin được xử lý và đi qua parser.

    ```log
    [13:32:39.961500] [bmv2] [D] [thread 56326] [58.0] [cxt 0] Processing packet received on port 1
    [13:32:39.961515] [bmv2] [D] [thread 56326] [58.0] [cxt 0] Parser 'parser': start
    [...]
    ```

    Khi parse:
    - Các bit được parse sẽ được sao chép vào cấu trúc được định nghĩa trong chương trình.
    - Con trỏ đầu buffer của gói sẽ lùi lại một khoảng tương ứng với các số đã parse.

4. Các byte đã parse được bỏ khỏi phần buffer được cấp phát cho gói tin -> Kết thúc parser:

    ```log
    [...]
    [13:32:39.949925] [bmv2] [T] [thread 56326] Popping 51 bytes from packet buffer (data size before pop: 51) - Buffer size before pop is 563
    [13:32:39.949929] [bmv2] [T] [thread 56326] Data size after pop: 0
    [13:32:39.949933] [bmv2] [D] [thread 56326] [57.0] [cxt 0] Parser 'parser': end
    ```

    Các đoạn mã thực hiện việc xoá phần đã được parse (Sao chép giá trị vào cấu trúc) khỏi PacketBuffer bao gồm:

    Dòng 1164 của file `src/bm_sim/parser.cpp`

    ```cpp
    void
    Parser::parse(Packet *pkt) const {
    [...]
        // dòng 1164
        pkt->remove(bytes_parsed); // hàm remove được gọi từ class Packet
    [...]
    }
    ```

    Dòng 209 của file `include/bm/bm_sim/packet.h` (hàm `Packet::remove`):

    ```cpp
    char *remove(size_t bytes) {
        assert(buffer.get_data_size() >= payload_size + bytes);
        return buffer.pop(bytes); // hàm pop được gọi từ class PacketBuffer
    }
    ```

    Dòng 102 của file `include/bm/bm_sim/packet_buffer.h` (hàm `PacketBuffer::pop`):

    ```cpp
    char *pop(size_t bytes) {
        BMLOG_TRACE("Popping {} bytes from packet buffer (data size before pop: {}) - Buffer size is {}",bytes, data_size, size);
        assert(bytes <= data_size);
        data_size -= bytes;
        head += bytes;
        BMLOG_TRACE("Data size after pop: {}", data_size);
        return head;
    }
    ```

5. Các thông tin đã parse vào cấu trúc sẽ được chuyển vào ingress, trong khi phần chưa parse ở lại trong buffer:

    ```log
    [13:32:39.949938] [bmv2] [D] [thread 56326] [57.0] [cxt 0] Pipeline 'ingress': start
    ```

    Trong mã nguồn của BMv2, ingress và egress không thể can thiệp vào buffer chưa parse của gói tin. Lý do là V1Model định nghĩa kiến trúc Ingress không nhận một tham số nào liên quan đến buffer của gói tin, mà chỉ nhận các tham số là header, metadata và standard_metadata. (dòng 28 của file `p4include/v1model.p4`)

    ```p4
    control Ingress<H, M>(inout H hdr,
                      inout M meta,
                      inout standard_metadata_t standard_metadata);
    ```

    Như vậy, để can thiệp vào payload của gói tin trong ingress, cần phải lấy chúng từ buffer vào một cấu trúc (cấu trúc có thể là header hoặc payload).

6. Theo kiến trúc V1Model, gói tin sẽ đi từ ingress sang egressbuffer trước khi vào egress. V1Model không có deparser cuối ingress và parser đầu egress (chỉ có parser đầu ingress và deparser cuối egress).

    ```log
    [13:32:40.129346] [bmv2] [D] [thread 56326] [69.0] [cxt 0] Pipeline 'ingress': end
    [13:32:40.129350] [bmv2] [D] [thread 56326] [69.0] [cxt 0] Egress port is 2
    [13:32:40.131152] [bmv2] [D] [thread 56329] [69.0] [cxt 0] Pipeline 'egress': start
    [...]
    [13:32:40.132662] [bmv2] [D] [thread 56329] [69.0] [cxt 0] Pipeline 'egress': end
    ```

    Tại cuối ingress (phương thức `SimpleSwitch::ingress_thread`), gói tin sẽ được đẩy vào egress buffer (phương thức `SimpleSwitch::enqueue`), trước khi kết thúc luồng của `ingress_thread`. (dòng 646 của file `target/simple_switch/simple_switch.cpp`)

    ```cpp
    SimpleSwitch::ingress_thread() {
    [...]
        // dòng 646
        enqueue(egress_port, std::move(packet));
    }
    ```

    Phương thức `SimpleSwitch::enqueue` sẽ đẩy gói tin vào egress buffer (bằng cách gọi phương thức `QueueingLogicPriRL::push_front(size_t queue_id, size_t priority, const T &item)`). (dòng 427 của file `target/simple_switch/simple_switch.cpp`)

    ```cpp
    egress_buffers.push_front(
        egress_port, priority,
        std::move(packet));
    ```

7. Deparser sẽ khởi động ngay sau khi egress kết thúc, các byte đã parse ở parser sẽ được đẩy về lại buffer

    ```log
    [13:32:40.132668] [bmv2] [D] [thread 56329] [69.0] [cxt 0] Deparser 'deparser': start
    [13:32:40.132674] [bmv2] [T] [thread 56329] Pushing 495 bytes to packet buffer (data size before push: 0) - Buffer size before push is 564
    ```

    Việc đẩy các byte đã parse về lại buffer được thực hiện tại các điểm sau:

    Dòng 77 file `src/bm_sim/deparser.cpp` (hàm `Deparser::deparse(Packet *pkt)`):

    ```cpp
    char *data = pkt->prepend(get_headers_size(*phv)); // hàm prepend được gọi từ class Packet
    ```

    Dòng 207 của file `include/bm/bm_sim/packet.h` (hàm `Packet::prepend`):

    ```cpp
    char *prepend(size_t bytes) { return buffer.push(bytes); } // hàm push được gọi từ class PacketBuffer
    ```

8. Gói tin được truyền ra ngoài theo lệnh emit.