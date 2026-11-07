# Ghi chú mã lõi `src/dpdp/` và thực nghiệm H1

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

Các gói `alns/`, `adaptations/` và `des/` đã có implementation cho ALNS-D,
đóng băng và mô phỏng sự kiện rời rạc. Pipeline H1 nằm trong
`experiments/H1_distance_freezing/`.

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

Hiện trạng H1: đã có ALNS-D, DES, đóng băng, baseline greedy, kiểm tra nghiệm
và pipeline chạy theo cặp. H1 vẫn là giả thuyết thực nghiệm, không phải kết
luận được giả định trước.

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
- Các toán tử phá/sửa, vòng lặp ALNS, mô phỏng sự kiện rời rạc và đóng băng đã
  có trong `src/dpdp/alns/`, `src/dpdp/des/` và `src/dpdp/adaptations/`.
  Bộ lọc ứng viên là phần mở rộng cho H2.
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

## Kết quả kiểm định H1 hiện tại

Đã chạy toàn bộ 56 instance Li & Lim (17 C, 23 R, 16 RC), 3 seed
(`0,1,2`), `rho=0.5`, ngân sách `0.05` giây, chân trời `1000` và đội xe
giới hạn `K=5`. Hai thuật toán dùng cùng instance, seed, release time và
ngân sách; ALNS-D dùng đóng băng.

Kết quả 168 cặp đều hợp lệ. ALNS-D thực sự thay đổi route ở 80/168 lần chạy
và cải thiện objective ở 80/168 lần. Tuy nhiên:

| Chỉ số | Greedy | ALNS-D + freezing | Wilcoxon (ALNS < greedy) |
|---|---:|---:|---:|
| Tổng quãng đường trung bình | 2699,176466 | 2703,249953 | p=0,07119516 |

Chênh lệch trung bình là `+4,073487`, tức ALNS-D cao hơn greedy khoảng
`0,1509%`. Vì `p > 0,05` và hướng chênh lệch không ủng hộ ALNS-D, **H1 chưa
được chứng minh/ủng hộ trong cấu hình này**. Đây là kết luận trung thực của
thực nghiệm, không phải lỗi pipeline. Kết quả nằm trong
[`../experiments/H1_distance_freezing/`](../experiments/H1_distance_freezing/).

## Việc NÊN làm tiếp (theo thứ tự)

1. Mở rộng số seed và ngân sách theo thiết kế đã chốt, không thay đổi hậu
   nghiệm để tìm kết quả có lợi.
2. Chuẩn hoá thang phạt `beta` theo Nhận xét 2.4.
3. Phân tích riêng theo họ C/R/RC và kiểm tra độ nhạy với `K`, `rho`, `B`.
4. Hiệu chỉnh `dynamize` theo công thức mục 1.3.1.
