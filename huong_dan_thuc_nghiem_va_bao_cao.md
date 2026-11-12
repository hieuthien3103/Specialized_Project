# ĐỒ ÁN CHUYÊN NGÀNH: NGHIÊN CỨU THUẬT TOÁN ADAPTIVE LARGE NEIGHBORHOOD SEARCH (ALNS) TRONG GIAO VẬN ĐÔ THỊ – ỨNG DỤNG ALNS CHO BÀI TOÁN GIAO NHẬN HÀNG ĐỘNG

Đây là tài liệu hướng dẫn tối cao (Master Context) dành cho AI Agent để hỗ trợ lập trình, chạy thực nghiệm và phân tích dữ liệu viết báo cáo (Chương 3, Kết luận) cho bài toán Dynamic Pickup and Delivery Problem (DPDP).

## 1. MỤC TIÊU VÀ KIẾN TRÚC ĐÁNH GIÁ (2 TẦNG)

* **Tầng 1 (Baseline Validation):** Chứng minh ALNS (có đóng băng) tạo ra lời giải tốt hơn thuật toán Greedy Insertion dưới cùng ngân sách thời gian.

* **Tầng 2 (Ablation Study - Giả thuyết H1-H4):** Bóc tách và đánh giá 3 cơ chế cải tiến của ALNS-D (Đóng băng, Lọc ứng viên, Cắt ngắn thời gian) tác động thế nào đến Chất lượng, Thời gian tính toán và Khả năng xử lý yêu cầu động.

## 2. KIẾN TRÚC THUẬT TOÁN (4 CỘT MỐC)

1. **Greedy Insertion:** Baseline chính (đại diện cho tốc độ phản hồi nhanh, "thiển cận").

2. **Regret-2 Insertion:** Baseline phụ (thông minh hơn Greedy, tránh so sánh với đối thủ quá yếu).

3. **ALNS Full:** Baseline lý tưởng (tái tối ưu toàn phần không đóng băng, không giới hạn ngân sách thời gian).

4. **ALNS-D:** Thuật toán thực tiễn đề xuất, bao gồm 3 cơ chế:

   * *Cơ chế đóng băng:* Không thay đổi phần lộ trình đã cam kết/đang di chuyển.

   * *Bộ lọc ứng viên:* Lọc theo độ lệch tuyến và hướng di chuyển để giảm không gian tìm kiếm.

   * *Cắt ngắn vòng lặp:* Dừng thuật toán dựa trên ngân sách thời gian thực (time budget), làm lạnh SA theo thời gian, kế thừa trọng số.
   * *Cơ chế tính điểm & chọn lọc (Roulette Wheel Selection):* Điều chỉnh trọng số thích nghi của các toán tử dựa trên cơ chế thưởng điểm ($\sigma_1$ cho lời giải tốt nhất toàn cục, $\sigma_2$ cho lời giải tốt hơn hiện tại, $\sigma_3$ cho  lời giải được chấp nhận).

## 3. THIẾT KẾ DỮ LIỆU & ÁNH XẠ KIỂM CHỨNG GIẢ THUYẾT (H1-H4)

**Hệ thống Dữ liệu:**

* **Dữ liệu Benchmark (Đối chứng):** Li & Lim (56 instances). Động hóa bằng cách gán thời điểm xuất hiện cho các yêu cầu dựa trên mức độ động $\rho \in \{0.25, 0.5, 0.75, 1\}$.
  * *Phân tách dữ liệu:* Calibration (dự kiến 12 instances) và Evaluation (44 instances). KHÔNG điều chỉnh tham số trên tập Evaluation.

* **Dữ liệu Thực tiễn (Bản đồ TP.HCM):** Sử dụng đồ thị đã trích xuất tại khu vực Quận 1 và Quận 3 (file `data/hcm/processed/q1_q3_hcmc.graphml`). 
  * *Quy mô:* 50-200 yêu cầu, 5-20 xe.
  * *Mục đích:* Khẳng định thuật toán hoạt động tốt trên ma trận khoảng cách/thời gian thực tế (tính bằng đường đi ngắn nhất trên đồ thị đường bộ, đảm bảo bất đẳng thức tam giác) thay vì khoảng cách hình học Euclidean.

**Liên kết Dữ liệu để giải quyết 4 Giả thuyết:**

* **Kiểm chứng H1 (Hiệu quả Đóng băng so với Tham lam):** Chạy ALNS-D (có đóng băng) và Greedy Insertion trên cùng tập Evaluation của Li & Lim với một mức ngân sách thời gian ($B$) cố định. So sánh tổng quãng đường ($D$).

* **Kiểm chứng H2 (Hiệu quả Bộ lọc ứng viên):** Bật/tắt bộ lọc ứng viên trên các instance có quy mô lớn của Li & Lim VÀ bộ dữ liệu TP.HCM (mạng lưới rộng, chi phí tìm đường cao) để đo lường mức độ giảm thời gian CPU ($\overline{t}_{dec}$) so với độ suy giảm của tổng quãng đường.

* **Kiểm chứng H3 (Đóng góp của cơ chế Thích nghi khi bị cắt ngắn):** Chạy thực nghiệm với ngân sách thời gian tái tối ưu ($B$) bị rút ngắn dần. Đánh giá xem phần đóng góp của trọng số thích nghi (Adaptive weights) có bị suy giảm về mức chọn ngẫu nhiên hay không.

* **Kiểm chứng H4 (Hiệu quả theo Mức độ động):** Quét thực nghiệm dọc theo các mức độ động $\rho \in \{0.25, 0.5, 0.75, 1\}$. Phân tích sự biến thiên của tỷ lệ phục vụ ($SR$), tỷ lệ từ chối ($RR$) và độ trễ ($L$) để chứng minh ALNS-D chống chịu tốt hơn khi đơn hàng động tăng lên.

## 4. TIÊU CHÍ ĐÁNH GIÁ (METRICS)

Hệ thống phải log lại các chỉ số sau cho mỗi lần chạy:

1. **Tổng quãng đường (**$D$**):** Đo chất lượng tối ưu (hàm mục tiêu).

2. **Tỷ lệ phục vụ (**$SR$**) / Tỷ lệ từ chối (**$RR$**):** Khả năng tiếp nhận đơn.

3. **Độ trễ (**$L, \overline{L}, L_{max}$**):** Số phút trễ so với khung thời gian (Time Windows).

4. **Xáo trộn lộ trình (**$\Xi_{assign}, \Xi_{eta}$**):** Tỷ lệ đổi xe và độ lệch giờ giao dự kiến trung bình.

5. **Thời gian tính toán (**$\overline{t}_{dec}$**):** Thời gian CPU thực tế cho mỗi lần quyết định.
6. **Định dạng xuất dữ liệu (Data Export):** Toàn bộ kết quả thực nghiệm phải được xuất ra định dạng `.csv` hoặc `.xlsx`. Cấu trúc quy định: mỗi dòng (row) là một lần chạy độc lập (1 instance + 1 cấu hình tham số + 1 seed) để phục vụ cho các kiểm định thống kê trên thư viện Pandas/SciPy sau này.

## 5. NGUYÊN TẮC PHÂN TÍCH VÀ BÁO CÁO (BẮT BUỘC TUÂN THỦ)

1. **Không định kiến:** Không đặt mục tiêu phải chứng minh ALNS-D luôn tốt hơn ALNS Full.

2. **Minh bạch dữ liệu:** Công bố cả kết quả tích cực, tiêu cực và không có ý nghĩa thống kê. KHÔNG cherry-pick (chỉ chọn seed/instance đẹp).

3. **Thống kê chuẩn mực:** Phân biệt rõ số instance, số seed và số kịch bản động. Dùng kiểm định Wilcoxon signed-rank. Nếu $p > 0.05$, chỉ được kết luận "chưa đủ bằng chứng để bác bỏ", tuyệt đối không kết luận "hai thuật toán tương đương".

4. **Tư duy Đánh đổi (Trade-off):** Nếu ALNS-D kém ALNS Full (ví dụ: quãng đường dài hơn), phải phân tích đó là sự đánh đổi cần thiết để đổi lấy tính ổn định (không xáo trộn lộ trình) và đáp ứng ràng buộc thời gian tính toán thực tế.

5. **Giới hạn & Hướng phát triển:** Nhận diện rõ bộ lọc ứng viên là heuristic (có thể loại nhầm xe tối ưu).

## 6. QUY TẮC LẬP TRÌNH CHO AI AGENT

* **Ngôn ngữ & Thư viện thuật toán:** Sử dụng Python, `alns` (Wouda và Lan), NumPy/Pandas.
* **Toán tử ALNS cụ thể (Operators):** Bắt buộc triển khai nhóm Destroy (Random Removal, Worst Removal, Shaw/Relatedness Removal) và nhóm Repair (Greedy Insertion, Regret-2, Regret-3 Insertion).
* **Xử lý Không gian & Bản đồ:** BẮT BUỘC sử dụng `osmnx` và `networkx` để parse dữ liệu `.osm.pbf` hoặc `.graphml`, sinh đồ thị giao thông có hướng và tính toán ma trận đường đi ngắn nhất cho tập dữ liệu thực tế TP.HCM.
* **Reproducibility:** Luôn fix `random.seed()` và `np.random.seed()` tại mỗi lần chạy thử nghiệm.
* **Kiến trúc Code:** Module hóa rõ ràng trong `experiments/` và `src/`.
* **Phản hồi:** Luôn dùng tiếng Việt, giải thích cơ sở thuật toán theo đúng chuẩn hàn lâm.
