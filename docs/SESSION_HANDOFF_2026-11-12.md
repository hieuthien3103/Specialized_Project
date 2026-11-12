# Bàn giao tiến độ DPDP/ALNS-D (12-11-2026)

Tài liệu này ghi lại trạng thái sau khi cập nhật mô hình DES và chạy lại hiệu
chỉnh tham số, H1 và H4. Dùng như ghi chú khởi động cho phiên làm việc tiếp theo.

## Tóm tắt

- Mô hình mô phỏng hiện tái tối ưu theo sự kiện yêu cầu mới đến; chưa mô phỏng
  chuyển động thực tế của xe hay tái tối ưu theo chu kỳ.
- Đã hiệu chỉnh tham số trên tập instance `lc102`, `lr102`, `lrc102`, rồi đánh
  giá trên tập tách biệt `lc101`, `lr101`, `lrc101`.
- Các lần chạy mới của H1 (120 dòng) và H4 (480 dòng) đều hợp lệ theo bộ kiểm
  tra. Kiểm thử dự án trước đó đạt **55 passed**.
- Đây vẫn là kết quả thực nghiệm hiện tại, không giải quyết yêu cầu của giảng
  viên về nguồn mã/thuật toán đối chứng: greedy và regret-2 đang do dự án tự
  triển khai.
- Các thay đổi đang nằm trong working tree, chưa được commit.

## Công việc đã thực hiện

### Mã và mô hình

- Bổ sung kiểm soát release time để điểm pickup không được phục vụ trước thời
  điểm yêu cầu xuất hiện; bộ checker độc lập cũng nhận và kiểm tra release time.
- Duy trì tập yêu cầu đã cam kết qua các bước destroy/repair của ALNS, tránh
  làm rơi yêu cầu đã được phục vụ/cam kết.
- Chuyển DES sang xử lý sự kiện yêu cầu đến và tái tối ưu ngay tại sự kiện đó.
  Chân trời đóng băng dùng công thức `H = time_scale × budget + H₀`.
- `H₀` có cùng đơn vị thời gian với instance. `time_scale` quy đổi ngân sách CPU
  vào chân trời đóng băng; CPU không làm thời gian mô phỏng tiến và kế hoạch
  được áp dụng ngay.
- Sửa kiểm thử đóng băng cho phép `min_pos = 0`, kiểm tra công thức H, và thay
  giả định không đúng về quãng đường phải đơn điệu theo mức độ động bằng kiểm
  tra phù hợp hơn.

### Hiệu chỉnh và thực nghiệm

- Hiệu chỉnh dùng các instance 102, đánh giá dùng các instance 101; K được lấy
  theo cấu hình tight ghi trong manifest:
  - `lc101=10`, `lr101=21`, `lrc101=17`
  - `lc102=10`, `lr102=18`, `lrc102=19`
- Lưới hiệu chỉnh có 81 cấu hình hợp lệ. Một lỗi chọn cấu hình do so sánh
  boolean `True` với chuỗi `"True"` đã được sửa.
- Cấu hình được chọn: `C2_H0_0`, `budget=0.05`, `H₀=0`, `time_scale=1`;
  overrides gồm `destroy_fraction=0.3`, `reaction=0.1`, `segment_min=10`.
- H1 có 120 dòng hợp lệ, 30 cặp cho mỗi thuật toán. So sánh ALNS-D với ALNS
  không đóng băng:
  - Chênh lệch trung bình quãng đường: `-9.83`, Wilcoxon hai phía `p=0.0929`.
  - Chênh lệch tỷ lệ phục vụ: `-0.0044`, `p=0.0588`.
  - Số lần đổi tuyến: `p=0.394`.
  - Chưa quan sát thấy khác biệt có ý nghĩa thống kê ở ngưỡng 0.05.
- H4 có 480 dòng hợp lệ, 30 cặp cho mỗi mức `rho` và thuật toán. So sánh
  ALNS-D với ALNS không đóng băng về quãng đường không có ý nghĩa thống kê tại
  các mức `rho` (`p` khoảng 0.575–0.859).
- Với ALNS-D, tỷ lệ phục vụ trung bình mô tả giảm từ khoảng 98.49% (`rho=0.25`)
  xuống 96.60% (`rho=1.0`); quãng đường trung bình tăng từ khoảng 1457.71 lên
  1475.87. Đây là xu hướng mô tả, chưa phải kiểm định xu hướng riêng.
- Ngân sách dừng theo thời gian CPU khiến cùng seed/release không nhất thiết
  tạo đúng cùng số vòng lặp hoặc cùng kết quả giữa hai lần chạy. So sánh trong
  mỗi batch được ghép cặp theo thiết kế chạy của batch đó.

### Báo cáo và tài liệu

- Đồng bộ báo cáo DOCX với mô hình tái tối ưu theo sự kiện, công thức chân trời
  đóng băng và giới hạn mô phỏng.
- Cập nhật README của H1/H4 và tài liệu dự án để chỉ cách chạy/phân tích các
  kết quả mới, tách chúng khỏi kết quả cũ.
- Analyzer thống kê cần SciPy (optional dependency `.[stats]`). H4 analyzer
  chạy thành công theo module invocation:
  `python -m experiments.H4_dynamism.analysis.analyze_h4`.

## Tệp kết quả quan trọng

- Cấu hình hiệu chỉnh: [selected_alns.json](../experiments/H1_distance_freezing/configs/selected_alns.json)
- Lưới và kết quả hiệu chỉnh:
  [calibration_grid.json](../experiments/H1_distance_freezing/configs/calibration_grid.json),
  [calibration.csv](../experiments/H1_distance_freezing/results/raw/calibration.csv)
- H1:
  [raw](../experiments/H1_distance_freezing/results/raw/h1_event_model.csv),
  [summary](../experiments/H1_distance_freezing/analysis/tables/h1_event_summary.csv)
- H4:
  [raw](../experiments/H4_dynamism/results/raw/h4_event_model.csv),
  [summary](../experiments/H4_dynamism/analysis/tables/h4_event_summary.csv)
- Manifest dữ liệu động: [manifest.json](../data/dynamic/manifest.json)
- Ghi chú cấu trúc và mã lõi: [README_dpdp_project.md](./README_dpdp_project.md)
- Báo cáo giữa kỳ: [Bao_cao_giua_ky_DACN_ALNS_DPDP.docx](../Bao_cao_giua_ky_DACN_ALNS_DPDP.docx)

## Việc cần làm tiếp

1. **Giải quyết nguồn thuật toán đối chứng trước khi chốt kết luận.** Các hàm
   greedy và regret-2 trong `src/dpdp/baselines.py` là triển khai của dự án,
   chưa phải mã được lấy nguyên từ nguồn ngoài. Trao đổi với giảng viên xem
   chấp nhận triển khai theo mô tả thuật toán có trích dẫn hay bắt buộc dùng
   mã nguồn công bố; nếu bắt buộc, xác định nguồn, giấy phép và cách bảo toàn
   ràng buộc DPDP trước khi thay baseline.
2. Khi đổi baseline hoặc thiết kế chạy, chạy lại các thí nghiệm bị ảnh hưởng
   và ghi rõ phiên bản mã/cấu hình đi cùng kết quả.
3. Hoàn thiện Chương 3 bằng môi trường, mô tả dữ liệu, nguồn thuật toán, tiêu
   chí đánh giá, quy tắc hiệu chỉnh, bảng kết quả H1/H4, kiểm định và giới hạn.
4. Nêu rõ kết quả hiện tại chưa chứng minh ưu thế thống kê của ALNS-D so với
   ALNS toàn phần; với cấu hình chọn `H₀=0`, hai phương pháp có thể khá gần
   nhau.
5. Mở rộng seed/số instance theo thiết kế thống kê đã định trước nếu cần tăng
   độ tin cậy; không chọn lại cấu hình dựa trên tập đánh giá.
6. Kiểm tra working tree và chạy lại kiểm thử trước khi commit. Tại thời điểm
   ghi tài liệu này, có nhiều thay đổi chưa commit; không xóa hoặc hoàn tác
   chúng một cách mù quáng.

## Lưu ý về dữ liệu lớn

Tệp `vietnam-261107.osm.pbf` khoảng 317 MB vượt giới hạn tệp thông thường của
GitHub. Các lần chạy hiện tại dùng dữ liệu mạng đường đã xử lý, vì vậy không
cần đưa PBF vào commit thường; tệp này đã được `.gitignore` bỏ qua.
