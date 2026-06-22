import os
import json
import google.generativeai as genai

def diagnose():
    # 1. Đọc API Key từ config.json
    config_path = os.path.join("storage", "config.json")
    if not os.path.exists(config_path):
        print("[-] Không tìm thấy file cấu hình storage/config.json. Vui lòng chạy ứng dụng và cấu hình API Key trước.")
        return
        
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            settings = json.load(f)
    except Exception as e:
        print(f"[-] Lỗi đọc file cấu hình: {e}")
        return
        
    api_key = settings.get("gemini_api_key", "").strip()
    if not api_key:
        print("[-] Chưa cấu hình Gemini API Key trong config.json.")
        return
        
    print(f"[+] Đã đọc API Key (độ dài: {len(api_key)} ký tự).")
    
    # 2. Cấu hình Gemini
    genai.configure(api_key=api_key)
    
    print("[*] Đang kết nối tới máy chủ Google để truy vấn danh sách Model...")
    try:
        models = genai.list_models()
        available_models = []
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
                
        print("\n[+] KẾT QUẢ: Kết nối thành công! Các models tài khoản của bạn có quyền sử dụng:")
        for model_name in available_models:
            prefix = "-> "
            if "gemini-1.5-flash" in model_name:
                prefix = "[Khuyên dùng] -> "
            print(f"  {prefix}{model_name}")
            
        if not any("gemini-1.5-flash" in name for name in available_models):
            print("\n[!] CẢNH BÁO: Model 'gemini-1.5-flash' KHÔNG nằm trong danh sách các model khả dụng của API Key này.")
            
    except Exception as e:
        print("\n[-] KẾT QUẢ: Lỗi kết nối API!")
        print(f"    Chi tiết lỗi: {e}")
        print("\n[Gợi ý khắc phục]:")
        print("    1. Hãy chắc chắn rằng API Key này được tạo từ Google AI Studio (https://aistudio.google.com/).")
        print("    2. Kiểm tra xem mạng internet của bạn có đang chặn kết nối Google API hay không.")

if __name__ == "__main__":
    diagnose()
