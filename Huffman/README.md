# Huffman chuẩn tắc — hướng dẫn chạy

Ứng dụng Streamlit này minh họa nén và giải nén Huffman chuẩn tắc, hỗ trợ nhập
văn bản hoặc tải tệp lên để mã hóa, và tải tệp `.huf` để giải mã.

## Yêu cầu

- Python 3.9 trở lên
- Các thư viện được khai báo trong `requirements.txt`

## Cài đặt và chạy trên macOS/Linux

Mở Terminal, chuyển đến thư mục dự án:

```bash
cd /Users/admin/Downloads/Huffman
```

Tạo môi trường ảo (chỉ cần làm lần đầu):

```bash
python3 -m venv .venv
```

Kích hoạt môi trường ảo và cài thư viện:

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Chạy ứng dụng:

```bash
python -m streamlit run huffman_advanced_algorithms.py
```

Mở địa chỉ được in trong Terminal, thường là <http://localhost:8501>. Dùng
`Ctrl+C` trong Terminal để dừng ứng dụng. Khi dùng lại, vào thư mục dự án,
chạy `source .venv/bin/activate`, rồi chạy lệnh Streamlit ở trên. Gõ `deactivate`
để thoát môi trường ảo.

## Chạy trên Windows

Trong PowerShell, chuyển đến thư mục dự án và tạo môi trường ảo:

```powershell
cd "$HOME\Downloads\Huffman"
py -m venv .venv
```

Kích hoạt và cài thư viện:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Chạy ứng dụng:

```powershell
python -m streamlit run huffman_advanced_algorithms.py
```

## Sử dụng

### Mã hóa

1. Mở tab **Mã hóa**.
2. Nhập văn bản hoặc chọn tệp bất kỳ để tải lên. Nếu chọn tệp, tệp đó được ưu
   tiên hơn văn bản đã nhập.
3. Nhấn **Mã hoá**.
4. Xem bảng ký tự/byte và mã Huffman, chuỗi bit, biểu đồ và các chỉ số như thời
   gian mã hóa, mức tiết kiệm, entropy và CRC-32.
5. Nhấn nút tải xuống để lưu tệp `.huf`.

Tệp văn bản UTF-8 có thêm phần hiển thị ký tự Unicode. Tệp nhị phân được mã hóa
theo byte; bảng ký tự Unicode sẽ không hiển thị. Tên tệp `.huf` được tạo từ tên
tệp đầu vào.

### Giải mã

1. Mở tab **Giải mã**.
2. Chọn tệp `.huf`.
3. Nhấn **Giải mã** để xem kết quả, thời gian giải mã và trạng thái kiểm tra
   CRC-32.
4. Tải dữ liệu đã giải mã xuống. Nếu nội dung là UTF-8 hợp lệ, ứng dụng cũng
   hiển thị văn bản đã khôi phục.

## Khắc phục lỗi `zsh: command not found: streamlit`

Hãy kích hoạt môi trường ảo trước khi chạy. Có thể gọi Streamlit thông qua
Python để không phụ thuộc vào lệnh `streamlit` trên `PATH`:

```bash
source .venv/bin/activate
python -m streamlit run huffman_advanced_algorithms.py
```

Nếu chưa cài thư viện, chạy `python -m pip install -r requirements.txt` trong
môi trường ảo trước.
