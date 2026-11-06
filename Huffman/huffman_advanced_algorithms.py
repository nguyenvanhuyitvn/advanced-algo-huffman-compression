"""
Huffman File Compression Implementation (Full Canonical Specification)
Advanced Algorithms Midterm Exam
Compliant with report: Magic HUF1, Canonical Codes, CRC-32, Bit-packing
Author: Nguyen Van Huy
"""
import heapq
import struct
import zlib
import math
import time
from collections import Counter
from typing import Dict, List, Tuple, Optional


class HuffmanNode:
    """Nút biểu diễn cây Huffman có cơ chế so sánh tất định (Deterministic Tie-breaking)"""
    def __init__(self, freq: int, seq: int, byte_val: Optional[int], left=None, right=None):
        self.freq = freq
        self.seq = seq
        self.byte_val = byte_val
        self.left = left
        self.right = right

    def __lt__(self, other: 'HuffmanNode') -> bool:
        if self.freq != other.freq:
            return self.freq < other.freq
        return self.seq < other.seq


class CanonicalHuffman:
    MAGIC = b"HUF1"

    @staticmethod
    def build_lengths(data: bytes) -> Tuple[Dict[int, int], int]:
        """Dựng cây Huffman và trích xuất độ dài từ mã len[] của từng byte"""
        if not data:
            return {}, 0
        freq = Counter(data)
        heap = []
        seq = 0
        for byte_val, count in sorted(freq.items(), key=lambda x: (x[1], x[0])):
            heap.append(HuffmanNode(count, seq, byte_val))
            seq += 1
        heapq.heapify(heap)

        if len(heap) == 1:
            return {heap[0].byte_val: 1}, len(data)

        while len(heap) > 1:
            left = heapq.heappop(heap)
            right = heapq.heappop(heap)
            seq += 1
            merged = HuffmanNode(left.freq + right.freq, seq, None, left=left, right=right)
            heapq.heappush(heap, merged)

        root = heap[0]
        lengths: Dict[int, int] = {}

        def _dfs(node: Optional[HuffmanNode], depth: int):
            if node is None:
                return
            if node.byte_val is not None:
                lengths[node.byte_val] = depth
                return
            _dfs(node.left, depth + 1)
            _dfs(node.right, depth + 1)

        _dfs(root, 0)
        return lengths, len(data)

    @staticmethod
    def generate_canonical_codes(lengths: Dict[int, int]) -> Dict[int, Tuple[int, int]]:
        """Sinh mã chuẩn tắc (Canonical Codes): trả về {byte: (code_int, bit_length)}"""
        if not lengths:
            return {}
        sorted_syms = sorted(lengths.items(), key=lambda x: (x[1], x[0]))
        canonical: Dict[int, Tuple[int, int]] = {}
        code = 0
        prev_len = sorted_syms[0][1]

        for byte_val, l in sorted_syms:
            code <<= (l - prev_len)
            canonical[byte_val] = (code, l)
            code += 1
            prev_len = l
        return canonical

    @classmethod
    def compress_bytes(cls, data: bytes) -> bytes:
        """Nén mảng byte theo Header chuẩn 18 + 2k byte và dòng bit thô"""
        if not data:
            return cls.MAGIC + struct.pack(">QIH", 0, 0, 0)

        crc = zlib.crc32(data) & 0xFFFFFFFF
        lengths, n_orig = cls.build_lengths(data)
        canonical = cls.generate_canonical_codes(lengths)

        # 1. Đóng gói Header: Magic(4B) + n(8B) + crc(4B) + k(2B) + k cặp (byte, len)
        k = len(lengths)
        header = bytearray(cls.MAGIC)
        header.extend(struct.pack(">QIH", n_orig, crc, k))
        for b_val, l in sorted(lengths.items()):
            header.extend(struct.pack(">BB", b_val, l))

        # 2. Đóng gói bit thực tế (Bit-packing vào từng byte)
        out_payload = bytearray()
        cur_byte = 0
        bits_count = 0

        for b in data:
            code, l = canonical[b]
            for shift in range(l - 1, -1, -1):
                bit = (code >> shift) & 1
                cur_byte = (cur_byte << 1) | bit
                bits_count += 1
                if bits_count == 8:
                    out_payload.append(cur_byte)
                    cur_byte = 0
                    bits_count = 0

        if bits_count > 0:
            cur_byte <<= (8 - bits_count)
            out_payload.append(cur_byte)

        return bytes(header + out_payload)

    @classmethod
    def decompress_bytes(cls, comp_data: bytes) -> bytes:
        """Giải nén, kiểm tra Magic, kiểm định Kraft và đối soát CRC-32"""
        if len(comp_data) < 18:
            raise ValueError("Tệp nén quá nhỏ hoặc sai định dạng.")

        magic = comp_data[:4]
        if magic != cls.MAGIC:
            raise ValueError("Sai Magic Bytes! Không phải định dạng HUF1.")

        n_orig, orig_crc, k = struct.unpack(">QIH", comp_data[4:18])
        if n_orig == 0:
            return b""

        offset = 18
        lengths: Dict[int, int] = {}
        for _ in range(k):
            b_val, l = struct.unpack(">BB", comp_data[offset:offset + 2])
            lengths[b_val] = l
            offset += 2

        # Kiểm định bất đẳng thức Kraft
        kraft_sum = sum(2 ** (-l) for l in lengths.values())
        if k > 1 and round(kraft_sum, 6) != 1.0:
            raise ValueError("Cảnh báo: Vi phạm bất đẳng thức Kraft! Cây không đầy đủ.")

        # Tái tạo bảng mã chuẩn tắc
        canonical = cls.generate_canonical_codes(lengths)
        code_to_byte = {v: k for k, v in canonical.items()}

        payload = comp_data[offset:]
        decompressed = bytearray()
        cur_code = 0
        cur_len = 0
        recovered = 0

        for byte_in in payload:
            for shift in range(7, -1, -1):
                bit = (byte_in >> shift) & 1
                cur_code = (cur_code << 1) | bit
                cur_len += 1

                if (cur_code, cur_len) in code_to_byte:
                    decompressed.append(code_to_byte[(cur_code, cur_len)])
                    recovered += 1
                    cur_code = 0
                    cur_len = 0
                    if recovered == n_orig:
                        break
            if recovered == n_orig:
                break

        # Kiểm tra tính toàn vẹn CRC-32
        actual_crc = zlib.crc32(decompressed) & 0xFFFFFFFF
        if actual_crc != orig_crc:
            raise ValueError("Lỗi CRC-32 Mismatch! Dữ liệu bị hỏng hoặc suy hao.")

        return bytes(decompressed)


def render_streamlit_app() -> None:
    """Giao diện trực quan để thử nghiệm nén và giải nén Huffman."""
    import streamlit as st

    st.set_page_config(page_title="Trực quan hóa Huffman", page_icon="🗜️", layout="wide")
    st.title("🗜️ Trực quan hóa nén Huffman chuẩn tắc")
    st.write(
        "Nhập văn bản để theo dõi quá trình mã hóa, hoặc tải tệp `.huf` "
        "để giải mã và kiểm tra toàn vẹn dữ liệu."
    )

    def byte_label(value: int) -> str:
        if value == 32:
            return "SPACE (0x20)"
        if 33 <= value <= 126:
            return f"{chr(value)} (0x{value:02X})"
        return f"0x{value:02X}"

    encode_tab, decode_tab = st.tabs(["Mã hóa", "Giải mã"])

    with encode_tab:
        with st.form("huffman_encode_form"):
            text = st.text_area(
                "Văn bản đầu vào (được mã hóa thành UTF-8)",
                value="",
                height=130,
            )
            source_file = st.file_uploader(
                "Hoặc tải tệp bất kỳ lên để mã hóa",
                help="Nếu vừa nhập văn bản vừa tải tệp, tệp được ưu tiên.",
            )
            st.form_submit_button("Mã hoá", type="primary", width="stretch")
        input_text: Optional[str] = text if source_file is None else None
        if source_file is not None:
            raw_data = source_file.getvalue()
            source_name = source_file.name.replace("\\", "/").rsplit("/", 1)[-1]
            source_stem = source_name.rsplit(".", 1)[0] if "." in source_name else source_name
            output_file_name = f"{source_stem or 'huffman_compressed'}.huf"
            try:
                input_text = raw_data.decode("utf-8")
            except UnicodeDecodeError:
                input_text = None
            st.caption(
                f"Đang mã hóa tệp **{source_name}** ({len(raw_data):,} byte)."
            )
        else:
            raw_data = text.encode("utf-8")
            output_file_name = "huffman_compressed.huf"
        compression_started = time.perf_counter()
        compressed = CanonicalHuffman.compress_bytes(raw_data)
        compression_time = time.perf_counter() - compression_started
        st.session_state["huffman_latest_compressed"] = compressed

        frequencies = Counter(raw_data)
        lengths, _ = CanonicalHuffman.build_lengths(raw_data)
        canonical = CanonicalHuffman.generate_canonical_codes(lengths)
        header_size = 18 + 2 * len(lengths)
        payload_size = len(compressed) - header_size
        crc = zlib.crc32(raw_data) & 0xFFFFFFFF

        st.subheader("Các bước mã hóa")
        step_columns = st.columns(4)
        for column, number, title, description in zip(
            step_columns,
            ("1", "2", "3", "4"),
            ("Đếm byte", "Tạo mã", "Đóng gói", "Kiểm tra"),
            (
                "Thống kê tần suất từng byte UTF-8.",
                "Tạo độ dài và mã Huffman chuẩn tắc.",
                "Ghi header HUF1 và chuỗi bit.",
                "Giải nén thử và đối chiếu CRC-32.",
            ),
        ):
            column.markdown(f"### {number}. {title}")
            column.caption(description)

        metrics = st.columns(5)
        metrics[0].metric("Kích thước gốc", f"{len(raw_data):,} B")
        metrics[1].metric("Số byte phân biệt", f"{len(frequencies):,}")
        metrics[2].metric("Kích thước tệp HUF", f"{len(compressed):,} B")
        if raw_data:
            savings = (1 - len(compressed) / len(raw_data)) * 100
            metrics[3].metric("Mức tiết kiệm", f"{savings:+.2f}%")
        else:
            metrics[3].metric("Mức tiết kiệm", "—")
        metrics[4].metric("Thời gian mã hóa", f"{compression_time * 1000:.3f} ms")
        st.caption(
            "Thời gian mã hóa chỉ đo thao tác nén dữ liệu, không bao gồm thời gian tải tệp."
        )
        if raw_data:
            st.caption(
                "Mức tiết kiệm âm nghĩa là tệp HUF lớn hơn dữ liệu gốc do phần header."
            )

        if raw_data:
            entropy = -sum(
                (count / len(raw_data)) * math.log2(count / len(raw_data))
                for count in frequencies.values()
            )
            average_length = sum(
                count * canonical[value][1] for value, count in frequencies.items()
            ) / len(raw_data)
            encoded_data_bits = sum(
                count * canonical[value][1] for value, count in frequencies.items()
            )
            kraft_sum = sum(2 ** (-length) for length in lengths.values())
            st.markdown("#### Thông số quan sát")
            stat_columns = st.columns(4)
            stat_columns[0].metric("Entropy Shannon H(X)", f"{entropy:.4f} bit/byte")
            stat_columns[1].metric("Độ dài mã trung bình", f"{average_length:.4f} bit/byte")
            stat_columns[2].metric("Payload trước padding", f"{encoded_data_bits:,} bit")
            stat_columns[3].metric("Tổng Kraft", f"{kraft_sum:.6f}")
            st.caption(
                f"Kiểm chứng Shannon: {entropy:.4f} ≤ {average_length:.4f} "
                f"< {entropy + 1:.4f} bit/byte."
            )

            symbol_rows = [
                {
                    "Byte UTF-8": byte_label(value),
                    "Tần suất": count,
                    "Độ dài mã (bit)": lengths[value],
                    "Mã chuẩn tắc": format(canonical[value][0], f"0{lengths[value]}b"),
                }
                for value, count in sorted(
                    frequencies.items(), key=lambda item: (-item[1], item[0])
                )
            ]
            chart_rows = symbol_rows[:40]
            chart_columns = st.columns(2)
            with chart_columns[0]:
                st.markdown("#### Biểu đồ tần suất byte")
                st.bar_chart(
                    {
                        "Byte": [row["Byte UTF-8"] for row in chart_rows],
                        "Tần suất": [row["Tần suất"] for row in chart_rows],
                    },
                    x="Byte",
                    y="Tần suất",
                )
            with chart_columns[1]:
                st.markdown("#### Độ dài mã theo byte")
                st.bar_chart(
                    {
                        "Byte": [row["Byte UTF-8"] for row in chart_rows],
                        "Độ dài mã (bit)": [
                            row["Độ dài mã (bit)"] for row in chart_rows
                        ],
                    },
                    x="Byte",
                    y="Độ dài mã (bit)",
                )
            st.caption("Biểu đồ hiển thị tối đa 40 byte có tần suất cao nhất.")
            st.markdown("#### Bảng mã theo byte")
            st.dataframe(symbol_rows, width="stretch", hide_index=True)
            st.caption(
                "Huffman mã hóa byte, không mã hóa trực tiếp ký tự Unicode. "
                "Ký tự ASCII thường chiếm 1 byte; ký tự như tiếng Việt có dấu hoặc emoji "
                "có thể gồm nhiều byte UTF-8."
            )

            if input_text is not None:
                character_frequencies = Counter(input_text)
                character_rows = []
                for character, count in sorted(
                    character_frequencies.items(), key=lambda item: (-item[1], ord(item[0]))
                ):
                    character_bytes = character.encode("utf-8")
                    byte_codes = [
                        format(canonical[value][0], f"0{canonical[value][1]}b")
                        for value in character_bytes
                    ]
                    character_rows.append(
                        {
                            "Ký tự": repr(character),
                            "Unicode": f"U+{ord(character):04X}",
                            "Tần suất ký tự": count,
                            "Byte UTF-8 (hex)": " ".join(
                                f"{value:02X}" for value in character_bytes
                            ),
                            "Mã Huffman từng byte": " | ".join(
                                f"{value:02X} → {code}"
                                for value, code in zip(character_bytes, byte_codes)
                            ),
                            "Chuỗi bit của ký tự": " ".join(byte_codes),
                        }
                    )

                st.markdown("#### Ký tự → byte UTF-8 → mã Huffman")
                st.dataframe(character_rows, width="stretch", hide_index=True)
                st.caption(
                    "Mỗi dòng là một ký tự Unicode riêng biệt. Với ký tự nhiều byte, "
                    "mỗi byte có một mã Huffman riêng; các nhóm bit được ghép theo thứ tự UTF-8."
                )

                sequence_rows = []
                for character in input_text[:24]:
                    character_bytes = character.encode("utf-8")
                    byte_codes = [
                        format(canonical[value][0], f"0{canonical[value][1]}b")
                        for value in character_bytes
                    ]
                    sequence_rows.append(
                        {
                            "Ký tự đầu vào": repr(character),
                            "Byte UTF-8": " ".join(
                                f"{value:02X}" for value in character_bytes
                            ),
                            "Mã bit theo byte": " ".join(byte_codes),
                        }
                    )

                st.markdown("#### Minh họa thứ tự mã hóa")
                st.dataframe(sequence_rows, width="stretch", hide_index=True)
                st.caption("Hiển thị tối đa 24 ký tự đầu vào.")
            else:
                st.info(
                    "Tệp không phải văn bản UTF-8 hợp lệ; các biểu đồ và mã hóa theo byte "
                    "vẫn có sẵn, còn bảng ký tự Unicode được ẩn."
                )

            encoded_bit_groups = [
                format(canonical[value][0], f"0{canonical[value][1]}b")
                for value in raw_data
            ]
            encoded_bit_stream = "".join(encoded_bit_groups)
            packed_payload = compressed[header_size:]
            packed_bit_stream = "".join(format(value, "08b") for value in packed_payload)
            padding_bits = len(packed_bit_stream) - len(encoded_bit_stream)

            with st.expander("Xem toàn bộ chuỗi bit sau mã hóa"):
                st.metric("Số bit dữ liệu Huffman", f"{len(encoded_bit_stream):,} bit")
                st.markdown("**Bit dữ liệu — nối mã Huffman của từng byte theo thứ tự đầu vào:**")
                st.code(
                    "\n".join(
                        encoded_bit_stream[index:index + 128]
                        for index in range(0, len(encoded_bit_stream), 128)
                    )
                    or "(không có bit dữ liệu)",
                    language="text",
                )
                st.caption(
                    "Xuống dòng chỉ để dễ đọc, không phải một phần của chuỗi bit."
                )
                st.markdown("**Payload thực tế sau khi đóng gói thành byte:**")
                st.code(
                    "\n".join(
                        packed_bit_stream[index:index + 128]
                        for index in range(0, len(packed_bit_stream), 128)
                    )
                    or "(payload rỗng)",
                    language="text",
                )
                st.caption(
                    f"Payload gồm {len(packed_payload):,} byte; có {padding_bits} bit đệm "
                    "ở cuối (nếu có) để đủ bội số 8 bit."
                )
        else:
            st.info("Văn bản đang rỗng; định dạng HUF1 vẫn có header 18 byte.")

        st.markdown("#### Cấu trúc tệp HUF1")
        package_columns = st.columns(6)
        package_parts = (
            ("Magic", 4, "HUF1"),
            ("Kích thước gốc", 8, "byte"),
            ("CRC-32", 4, f"0x{crc:08X}"),
            ("Số mã (k)", 2, str(len(lengths))),
            ("Bảng độ dài", 2 * len(lengths), "2 byte/mã"),
            ("Payload", payload_size, "bit đã đóng gói"),
        )
        for column, (name, size, detail) in zip(package_columns, package_parts):
            column.metric(name, f"{size:,} B")
            column.caption(detail)
        st.download_button(
            "Tải tệp đã mã hóa (.huf)",
            data=compressed,
            file_name=output_file_name,
            mime="application/octet-stream",
            width="stretch",
        )

        verification_started = time.perf_counter()
        restored = CanonicalHuffman.decompress_bytes(compressed)
        verification_time = time.perf_counter() - verification_started
        if restored == raw_data:
            st.success(
                f"Giải nén xác minh thành công — CRC-32: 0x{crc:08X} "
                f"(thời gian: {verification_time * 1000:.3f} ms)."
            )
        else:
            st.error("Dữ liệu giải nén thử không khớp đầu vào.")

    with decode_tab:
        st.subheader("Giải mã tệp HUF1")
        with st.form("huffman_decode_form"):
            uploaded_file = st.file_uploader(
                "Chọn tệp Huffman (.huf)",
                type=["huf"],
                help="Tệp phải theo định dạng HUF1 do chương trình này tạo.",
            )
            decode_submitted = st.form_submit_button(
                "Giải mã", type="primary", width="stretch"
            )
        if decode_submitted and uploaded_file is not None:
            compressed_input = uploaded_file.getvalue()
            decompression_started = time.perf_counter()
            try:
                decompressed = CanonicalHuffman.decompress_bytes(compressed_input)
            except (ValueError, struct.error, IndexError) as error:
                st.error(f"Không thể giải mã tệp: {error}")
            else:
                decompression_time = time.perf_counter() - decompression_started
                st.success("Giải mã thành công; CRC-32 hợp lệ.")
                original_size = struct.unpack(">Q", compressed_input[4:12])[0]
                decoded_crc = zlib.crc32(decompressed) & 0xFFFFFFFF
                decode_metrics = st.columns(4)
                decode_metrics[0].metric("Kích thước tệp HUF", f"{len(compressed_input):,} B")
                decode_metrics[1].metric("Kích thước sau giải mã", f"{len(decompressed):,} B")
                decode_metrics[2].metric("CRC-32", f"0x{decoded_crc:08X}")
                decode_metrics[3].metric(
                    "Thời gian giải mã",
                    f"{decompression_time * 1000:.3f} ms",
                )
                if len(decompressed) != original_size:
                    st.warning("Kích thước sau giải mã không khớp thông tin trong header.")
                try:
                    decoded_text = decompressed.decode("utf-8")
                except UnicodeDecodeError:
                    st.info("Dữ liệu không phải văn bản UTF-8; cung cấp kết quả dưới dạng tệp nhị phân.")
                else:
                    st.text_area("Văn bản đã khôi phục", decoded_text, height=180)
                st.download_button(
                    "Tải dữ liệu đã giải mã",
                    data=decompressed,
                    file_name="huffman_decompressed.bin",
                    mime="application/octet-stream",
                    width="stretch",
                )
        elif decode_submitted:
            st.warning("Vui lòng chọn tệp `.huf` trước khi nhấn Giải mã.")
        else:
            st.info("Chọn tệp `.huf`, sau đó nhấn **Giải mã** để bắt đầu.")


if __name__ == "__main__":
    render_streamlit_app()