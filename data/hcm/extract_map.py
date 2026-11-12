import osmnx as ox
import os

def download_and_save_map():
    # 1. Định nghĩa khu vực cần lấy
    places = [
        "District 1, Ho Chi Minh City, Vietnam",
        "District 3, Ho Chi Minh City, Vietnam"
    ]
    
    print("Đang tải dữ liệu mạng lưới đường bộ từ OpenStreetMap...")
    # Tải đồ thị (network_type='drive' để lấy đường cho xe cộ)
    G = ox.graph_from_place(places, network_type='drive')
    
    # 2. Đảm bảo thư mục lưu trữ tồn tại
    output_dir = "data/hcm/processed"
    os.makedirs(output_dir, exist_ok=True)
    
    # 3. Lưu thành file .graphml vào đúng cấu trúc của bạn
    filepath = f"{output_dir}/q1_q3_hcmc.graphml"
    ox.save_graphml(G, filepath=filepath)
    
    print(f"Hoàn tất! Đã lưu đồ thị vào {filepath}")
    print(f"Số lượng nút (giao lộ): {len(G.nodes)}")
    print(f"Số lượng cạnh (đoạn đường): {len(G.edges)}")

if __name__ == "__main__":
    # Cấu hình osmnx in log ra console để theo dõi
    ox.settings.log_console = True
    ox.settings.use_cache = True
    download_and_save_map()