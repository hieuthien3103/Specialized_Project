# Khung mã ĐACN – ALNS cho bài toán giao nhận hàng động (bước 1–3)

Python ≥ 3.10, **không cần thư viện ngoài** (chỉ thư viện chuẩn).

## Cấu trúc
| File | Vai trò | Ứng với báo cáo |
|---|---|---|
| `dpdp/instance.py` | Đọc/ghi file Li & Lim, sinh dữ liệu thử, `dynamize` | mục 1.3.1 |
| `dpdp/route.py` | Lộ trình một xe, kiểm tra khả thi, tìm vị trí chèn tốt nhất, loại yêu cầu | mục 2.2.1, Bổ đề 2.1, Mệnh đề 1.2 |
| `dpdp/baselines.py` | `Solution`, chèn tham lam, chèn regret-2, `insert_request` | đối chứng ở mục "Công việc tiếp theo" |
| `dpdp/checker.py` | Bộ kiểm tra độc lập (không dùng lại mã của `route.py`) | ràng buộc (2.11)–(2.19) |
| `dpdp/cli.py` | Chạy hai thuật toán và in bảng kết quả | |
| `tests/test_core.py` | 10 kiểm thử | |

## Chạy
```
python tests/test_core.py
python -m dpdp.cli --instance lc101.txt            # file tải từ SINTEF
python -m dpdp.cli --instance lrc101.txt --vehicles 15 --late-max 10
python -m dpdp.cli --synthetic 100 --seed 2         # chỉ để gỡ lỗi
```

Mỗi lần chạy CLI vẫn in bảng kết quả ra terminal và đồng thời lưu CSV vào thư mục
`results/` (ví dụ `results/lc101_results.csv`). Có thể đổi thư mục bằng:
```
python -m dpdp.cli --instance lc101.txt --output-dir results
```
CSV ghi lại dữ liệu đầu vào, cấu hình chạy, kết quả của từng thuật toán và trạng
thái kiểm tra hợp lệ. CLI cũng lưu bảng dạng Terminal vào file tương ứng
(ví dụ `results/lc101_results.txt`) để dễ đọc hoặc chèn vào báo cáo.

## Việc NÊN làm đầu tiên
Mã đọc file theo mô tả định dạng trên trang SINTEF (9 trường: ID X Y DEMAND EARLIEST
LATEST SERVICE PICKUP DELIVERY; dòng đầu K Q S). Môi trường soạn mã không truy cập được
sintef.no nên **chưa chạy trên file Li & Lim thật**. Hãy tải một file (ví dụ `lc101.txt`)
và chạy `python -m dpdp.cli --instance lc101.txt`. Nếu parser báo lỗi, chỉ cần sửa
`parse_lilim` trong `instance.py`; phần còn lại không phụ thuộc định dạng file.

## Quyết định thiết kế cần đối chiếu với báo cáo
- **Khung thời gian**: điểm lấy cứng; điểm giao có cận trên mềm với độ trễ tối đa
  `late_max` (= L̄). `late_max = 0` cho đúng Li & Lim gốc.
- **Mục tiêu**: `alpha·quãng đường + gamma·độ trễ + beta·số yêu cầu bị từ chối`
  (công thức 2.1; giá trị mặc định 1 / 0,25 / 1000, hãy chuẩn hoá theo Nhận xét 2.4).
- **Số xe K**: lấy từ header của file, ghi đè bằng `--vehicles`. Li & Lim tối ưu số xe
  trước nên K lớn thì không bao giờ có đơn bị từ chối.
- **`dynamize`**: τ_r ~ U[0, l_p − t(0,p) − Λ] cho tỷ lệ ρ yêu cầu được chọn. Hãy đối chiếu
  với công thức ở mục 1.3.1 của báo cáo và sửa cho khớp.
- Lời giải tốt nhất đã biết trên SINTEF dùng mục tiêu thứ bậc (số xe, rồi quãng đường) nên
  **không so trực tiếp** được với mục tiêu ở đây; chỉ dùng để kiểm tra độ hợp lý.

## Hiệu năng và hạn chế hiện tại
- Kiểm tra chèn hiện là O(m) mỗi vị trí, có cắt tỉa và lối tắt "đuôi không đổi"; chưa dùng
  độ dãn thời gian O(1) như phân tích ở mục 2.2.7. Trên dữ liệu sinh, 100 yêu cầu chạy
  khoảng 0,1 giây mỗi thuật toán. Nếu cần nhanh hơn thì tối ưu `Route.best_insertion`.
- Chưa có: toán tử phá huỷ, vòng lặp ALNS, mô phỏng sự kiện rời rạc, đóng băng, bộ lọc ứng
  viên. Đó là các bước 4–6; `Route.remove_request` và `insert_request` đã sẵn để làm nền.
- `generate_synthetic` chỉ để gỡ lỗi, **không dùng để báo cáo kết quả**.
