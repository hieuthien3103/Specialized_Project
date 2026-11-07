# H1 — Đóng băng và quãng đường

Kiểm tra ALNS có ràng buộc đóng băng phần lộ trình đã cam kết có làm giảm tổng
quãng đường so với chiến lược chèn tham lam hay không.

- `configs/`: cấu hình instance, ngân sách và seed
- `results/`: kết quả chạy thô
- `analysis/`: tổng hợp, trung bình, độ lệch chuẩn và Wilcoxon theo cặp

## Chạy

Từ thư mục gốc repo:

```bash
python3 experiments/H1_distance_freezing/scripts/run_h1.py \
  --instances lc101.txt lr101.txt lrc101.txt \
  --seeds 0 1 2 3 4 5 6 7 8 9
python3 experiments/H1_distance_freezing/analysis/analyze_h1.py
```

Hai thuật toán dùng cùng instance, seed, mức độ động, ngân sách và đội xe:

- `greedy`: chèn tham lam ban đầu và gán yêu cầu mới khi xuất hiện;
- `alns_freezing`: ALNS-D tái tối ưu khi yêu cầu mới xuất hiện, với phần route
  đã cam kết bị đóng băng.

Kết quả từng cặp nằm ở `results/raw/h1_paired_results.csv`; bảng tổng hợp nằm
ở `analysis/tables/h1_summary.csv`. H1 chỉ được đánh giá sau khi chạy trên
dữ liệu Li & Lim thật và kiểm tra `total_distance` bằng Wilcoxon theo cặp.
