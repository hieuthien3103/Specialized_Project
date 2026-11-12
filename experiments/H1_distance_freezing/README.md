# H1 — Đóng băng và quãng đường

Kiểm tra ALNS-D với ràng buộc đóng băng phần lộ trình đã cam kết so với ba
đối chứng trên cùng một kịch bản động: greedy, regret-2 và ALNS tái tối ưu
toàn phần (`alns_full`).

- `configs/`: cấu hình instance, ngân sách và seed
- `results/`: kết quả chạy thô
- `analysis/`: tổng hợp, trung bình, độ lệch chuẩn và Wilcoxon theo cặp

## Chạy

Từ thư mục gốc repo:

```bash
python3 experiments/H1_distance_freezing/scripts/run_h1.py \
  --instances lc101.txt lr101.txt lrc101.txt \
  --seeds 0 1 2 3 4 5 6 7 8 9 \
  --rho 0.5 --vehicles 10 --budget 0.2 \
  --release-root data/dynamic
python3 experiments/H1_distance_freezing/analysis/analyze_h1.py
```

Hai thuật toán dùng cùng instance, seed, mức độ động, ngân sách và đội xe.
Mặc định thực nghiệm H1 dùng `--vehicles 5` thay vì K=25 của file Li & Lim,
để tạo không gian tái tối ưu có ràng buộc; giá trị này phải được báo cáo cùng
kết quả:

- `greedy`: chèn theo chi phí tăng thêm thấp nhất;
- `regret2`: chèn theo hối tiếc bậc hai;
- `alns_full`: tái tối ưu ALNS không bật cơ chế đóng băng;
- `alns_freezing`: ALNS-D có đóng băng.

Runner ghi thêm `served_rate`, `decision_seconds_mean` và
`decision_seconds_max`. Các cặp trong kiểm định phải có cùng instance, seed,
rho, budget, horizon và số xe; kiểm định Wilcoxon được thực hiện hai phía.

Kết quả từng cặp nằm ở `results/raw/h1_paired_results.csv`; bảng tổng hợp nằm
ở `analysis/tables/h1_summary.csv`. H1 chỉ được đánh giá sau khi chạy trên
dữ liệu Li & Lim thật và kiểm tra `total_distance` bằng Wilcoxon theo cặp.
