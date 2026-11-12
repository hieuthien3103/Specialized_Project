# H1 — Đóng băng và quãng đường

Kiểm tra ALNS-D với ràng buộc đóng băng phần lộ trình đã cam kết so với ba
đối chứng trên cùng một kịch bản động: greedy, regret-2 và ALNS tái tối ưu
toàn phần (`alns_full`).

- `configs/`: cấu hình instance, ngân sách và seed
- `results/`: kết quả chạy thô
- `analysis/`: tổng hợp, trung bình, độ lệch chuẩn và Wilcoxon theo cặp

## Hiệu chỉnh H₀ và chạy

Hiệu chỉnh trên tập riêng `lc102/lr102/lrc102`; K được lấy theo mức tight
trong manifest. Lưới khảo sát H₀ = 0, 10, 30 (đơn vị thời gian của instance):

```bash
python3 experiments/H1_distance_freezing/scripts/make_dynamic_data.py \
  --instances lc101.txt lr101.txt lrc101.txt lc102.txt lr102.txt lrc102.txt
python3 experiments/H1_distance_freezing/scripts/tune_parameters.py
```

Sau khi có `configs/selected_alns.json`, chạy H1/H4 với cùng cấu hình đã chọn.

Từ thư mục gốc repo:

```bash
python3 experiments/H1_distance_freezing/scripts/run_h1.py \
  --instances lc101.txt lr101.txt lrc101.txt \
  --seeds 0 1 2 3 4 5 6 7 8 9 \
  --rho 0.5 --fleet-level tight --selected-config \
  experiments/H1_distance_freezing/configs/selected_alns.json \
  --release-root data/dynamic \
  --output experiments/H1_distance_freezing/results/raw/h1_event_model.csv
python3 experiments/H1_distance_freezing/analysis/analyze_h1.py \
  --input experiments/H1_distance_freezing/results/raw/h1_event_model.csv \
  --output experiments/H1_distance_freezing/analysis/tables/h1_event_summary.csv
```

Các thuật toán dùng cùng instance, seed, mức độ động, ngân sách và đội xe.
`--fleet-level tight` lấy K theo manifest (lc101=10, lr101=21, lrc101=17).
Tham số `--freeze-horizon` là H₀ theo đơn vị thời gian của instance; chân trời
đóng băng được tính là H=ςB+H₀. Hiệu chỉnh H₀ được thực hiện trên các thể hiện
102 để tránh dùng tập đánh giá:

- `greedy`: chèn theo chi phí tăng thêm thấp nhất;
- `regret2`: chèn theo hối tiếc bậc hai;
- `alns_full`: tái tối ưu ALNS không bật cơ chế đóng băng;
- `alns_freezing`: ALNS-D có đóng băng.

Runner ghi thêm `served_rate`, `decision_seconds_mean` và
`decision_seconds_max`. Các cặp trong kiểm định phải có cùng instance, seed,
rho, budget, H₀, horizon và số xe; kiểm định Wilcoxon được thực hiện hai phía.

Kết quả của mô hình sự kiện hiện tại nằm ở `results/raw/h1_event_model.csv`;
bảng tổng hợp tương ứng nằm ở `analysis/tables/h1_event_summary.csv`. Không
ghi đè các kết quả cũ vì chúng được sinh từ mô hình mô phỏng trước đây. H1 chỉ được đánh giá sau khi chạy trên
dữ liệu Li & Lim thật và kiểm tra `total_distance` bằng Wilcoxon theo cặp.
