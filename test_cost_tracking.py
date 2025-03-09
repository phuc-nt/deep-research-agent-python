import requests
import json
import os
from datetime import datetime

def test_cost_tracking():
    """
    Kiểm tra API endpoint /research/{research_id}/cost với task ID đã tồn tại
    """
    # ID của task đã tồn tại
    task_id = "92808f8c-15ad-40c5-8825-01e0d2b16f76"
    
    print(f"Kiểm tra chi phí cho research task ID: {task_id}")
    
    # URL của API
    api_url = f"http://localhost:8000/api/v1/research/{task_id}/cost"
    
    try:
        # Gửi request GET đến API
        response = requests.get(api_url)
        response.raise_for_status()
        
        # Phân tích response JSON
        data = response.json()
        
        # Hiển thị thông tin chi phí
        print("\n===== THÔNG TIN CHI PHÍ =====")
        print(f"Tổng chi phí: ${data.get('total_cost_usd', 0):.6f} USD")
        print(f"Chi phí LLM: ${data.get('llm_cost_usd', 0):.6f} USD")
        print(f"Chi phí Search: ${data.get('search_cost_usd', 0):.6f} USD")
        print(f"Tổng tokens: {data.get('total_tokens', 0):,}")
        print(f"Tổng input tokens: {data.get('total_input_tokens', 0):,}")
        print(f"Tổng output tokens: {data.get('total_output_tokens', 0):,}")
        print(f"Tổng requests: {data.get('total_requests', 0):,}")
        
        # Hiển thị chi tiết từng model
        model_breakdown = data.get('model_breakdown', {})
        if model_breakdown:
            print("\nChi tiết theo model:")
            for model, model_data in model_breakdown.items():
                print(f"  - {model}: ${model_data.get('cost_usd', 0):.6f} USD ({model_data.get('requests', 0):,} requests)")
                if 'input_tokens' in model_data and 'output_tokens' in model_data:
                    print(f"    {model_data.get('input_tokens', 0):,} input tokens, {model_data.get('output_tokens', 0):,} output tokens")
        
        # Hiển thị chi tiết từng provider
        provider_breakdown = data.get('provider_breakdown', {})
        if provider_breakdown:
            print("\nChi tiết theo provider:")
            for provider, provider_data in provider_breakdown.items():
                print(f"  - {provider}: ${provider_data.get('cost_usd', 0):.6f} USD ({provider_data.get('requests', 0):,} requests)")
                if 'input_tokens' in provider_data and 'output_tokens' in provider_data:
                    print(f"    {provider_data.get('input_tokens', 0):,} input tokens, {provider_data.get('output_tokens', 0):,} output tokens")
        
        # Hiển thị thời gian thực hiện
        execution_time = data.get('execution_time_seconds', {})
        if execution_time:
            print("\nThời gian thực hiện:")
            for phase, seconds in execution_time.items():
                minutes = int(seconds) // 60
                remaining_seconds = seconds % 60
                time_str = f"{minutes} phút {remaining_seconds:.1f} giây" if minutes > 0 else f"{seconds:.1f} giây"
                print(f"  - {phase}: {time_str}")
        
        print("\n===== KẾT THÚC KIỂM TRA =====")
        
        # Lưu dữ liệu vào file json để kiểm tra sau
        output_dir = os.path.join("data", "test_output")
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = os.path.join(output_dir, f"cost_tracking_{task_id}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\nĐã lưu kết quả vào file: {output_file}")
        
        return True
    except Exception as e:
        print(f"Lỗi: {str(e)}")
        return False

if __name__ == "__main__":
    test_cost_tracking() 