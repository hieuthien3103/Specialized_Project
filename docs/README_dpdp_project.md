# Ghi chú mã lõi `src/dpdp/` (giai đoạn 1–3)

Python ≥ 3.10, **không cần thư viện ngoài** (chỉ thư viện chuẩn).

## Cấu trúc mã lõi

| File | Vai trò | Ứng với báo cáo |
|---|---|---|
| `src/dpdp/instance.py` | Đọc/ghi file Li & Lim, sinh dữ liệu thử, `dynamize` | mục 1.3.1 |
| `src/dpdp/route.py` | Lộ trình một xe, kiểm tra khả thi, tìm vị trí chèn tốt nhất, loại yêu cầu | mục 2.2.1, Bổ đề 2.1, Mệnh đề 1.2 |
| `src/dpdp/solution.py` | `Solution` (tập lộ trình + yêu cầu bị từ chối), `insert_request` | dùng chung ALNS + DES |
| `src/dpdp/baselines.py` | Chèn tham lam, chèn regret-2 | đối chứng ở mục "Công việc tiếp theo" |
| `src/dpdp/checker.py` | Bộ kiểm tra độc lập (không dùng lại mã của `route.py`) | ràng buộc (2.11)–(2.19) |
| `src/dpdp/paths.py` | Đường dẫn chuẩn `data/`, `experiments/`, metadata commit/timestamp | hỗ trợ tái lập |
| `src/dpdp/cli.py` | Chạy hai thuật toán và in bảng kết quả | |
| `tests/test_core.py` | 10 kiểm thử | |

Các gói `alns/`, `adaptations/`, `des/`, `evaluation/` là chỗ trống cho giai đoạn 4–6.

## Vai trò trong thực nghiệm H1–H4

Đây là nền tảng mã cho thực nghiệm H1 và các mở hiện H2–H4; **không sao chép mã
thành bốn phiên bản**. Cấu hình, script chạy, kết quả và phân tích theo giả thuyết
nằm trong [`../experiments/`](../experiments/).

| Giả thuyết | Mã đang dùng hoặc cần mở rộng | Dữ liệu/kết quả |
|---|---|---|
| H1 — đóng băng và quãng đường | **Thực nghiệm chính**; hiện có `route.py`, `baselines.py`, `checker.py`, `cli.py` làm nền cho baseline và ALNS | `experiments/H1_distance_freezing/` |
| H2 — bộ lọc ứng viên | `route.py` và `cli.py` làm nền; cần bổ sung bộ lọc | `experiments/H2_candidate_filter/` |
| H3 — trọng số thích nghi | `baselines.py` làm nền; cần bổ sung cập nhật trọng số | `experiments/H3_adaptive_weights/` |
| H4 — mức độ động | `instance.py` (`dynamize`, `degree_of_dynamism`), `cli.py` | `experiments/H4_dynamism/` |

Hiện trạng: đã có nền tảng DPDP và baseline nhưng **chưa có** ALNS, mô phỏng sự kiện
rời rạc, cơ chế đóng băng và bộ lọc ứng viên. Vì vậy, kết quả hiện tại **không
phải** là kết quả kiểm chứng hoàn chỉnh cho H1–H4.

## Chạy

```bash
python tests/test_core.py
python -m dpdp.cli --instance data/lilim/lc101.txt    # file Li & Lim thật
python -m dpdp.cli --instance lrc101.txt --vehicles 15 --late-max 10
python -m dpdp.cli --synthetic 100 --seed 2           # chỉ để gỡ lỗi
```

CLI in bảng kết quả ra terminal và lưu CSV + bảng văn bản vào
`experiments/H1_distance_freezing/results/raw/` (mặc định), kèm mã commit,
timestamp và phiên bản Python. Đổi thư mục bằng `--output-dir`.

## Tình trạng dữ liệu

Bộ Li & Lim **đã có** trong `data/lilim/` (56 file: lc*, lr*, lrc*). Parser đã
được kiểm thử trên `lc101.txt` (53 yêu cầu, K=25, Q=200).

## Quyết định thiết kế cần đối chiếu với báo cáo

- **Khung thời gian**: điểm lấy cứng; điểm giao có cận trên mềm với độ trễ tối đa
  `late_max` (= L̄). `late_max = 0` cho đúng Li & Lim gốc.
- **Mục tiêu**: `alpha·quãng đường + gamma·độ trễ + beta·số yêu cầu bị từ chối`
  (công thức 2.1; mặc định 1 / 0,25 / 1000 — **cần chuẩn hoá theo Nhận xét 2.4**).
- **Số xe K**: lấy từ header của file, ghi đè bằng `--vehicles`. Li & Lim tối ưu số xe
  trước nên K lớn thì không bao giờ có đơn bị từ chối.
- **`dynamize`**: τ_r ~ U[0, l_p − t(0,p) − Λ] cho tỷ lệ ρ yêu cầu được chọn. **Cần
  đối chiếu với công thức ở mục 1.3.1 của báo cáo và sửa cho khớp.**
- Lời giải tốt nhất đã biết trên SINTEF dùng mục tiêu thứ bậc (số xe, rồi quãng đường) nên
  **không so trực tiếp** được với mục tiêu ở đây; chỉ dùng để kiểm tra độ hợp lý.

## Hiệu năng và hạn chế hiện tại

- Kiểm tra chèn hiện là O(m) mỗi vị trí, có cắt tỉa và lối tắt "đuôi không đổi"; chưa dùng
  độ dãn thời gian O(1) như phân tích ở mục 2.2.7. Trên `lc101.txt`, mỗi thuật toán
  chạy ~0,01–0,02 giây. Nếu cần nhanh hơn thì tối ưu `Route.best_insertion`.
- Chưa có: toán tử phá huỷ, vòng lặp ALNS, mô phỏng sự kiện rời rạc, đóng băng, bộ lọc ứng
  viên. Đó là các bước 4–6; `Route.remove_request` và `insert_request` đã sẵn để làm nền.
- `generate_synthetic` chỉ để gỡ lỗi, **không dùng để báo cáo kết quả**.

## Ghi nhận từ thực nghiệm sơ bộ (2026-11)

Trên `lc101.txt` (K=25, L̄=0), hai thuật toán đối chứng cho kết quả:

| Thuật toán | Phục vụ | Số xe dùng | Quãng đường |
|---|---|---|---|
| greedy | 53/53 | 10 | 828,94 |
| regret-2 | 53/53 | 13 | 1411,88 |

`regret-2` cho quãng đường **tệ hơn** `greedy`: đây là hành vi đúng của thuật toán
(regret ưu tiên yêu cầu chỉ còn ít xe khả thi, kể cả khi rất đắt), không phải lỗi.
Cần kiểm tra lại khi hiệu chỉnh tham số ở giai đoạn 5 (Bảng 2.4), vì H1 so sánh
"chèn tham lam theo chi phí thấp nhất" với ALNS có đóng băng — nếu baseline quá mạnh
thì khó khẳng định H1.

## Việc NÊN làm tiếp (theo thứ tự)

1. Hiệu chỉnh `dynamize` theo công thức mục 1.3.1 (chặn H4).
2. Chuẩn hoá thang phạt `beta` theo Nhận xét 2.4 (chặn H1–H3, tránh mục tiêu bị
   chi phối bởi số đơn bị từ chối).
3. Cài đặt `alns/` + `adaptations/freezing.py` → chạy H1.
