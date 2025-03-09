import json
from datetime import datetime
from pathlib import Path

# Tạo dữ liệu cost monitoring cơ bản
cost_data = {
    'task_id': '7c6867f0-b822-4317-ae57-b0f4942312c3',
    'llm_requests': [],
    'search_requests': [],
    'phase_timings': [],
    'section_timings': [],
    'summary': {
        'total_cost_usd': 0.0,
        'llm_cost_usd': 0.0,
        'search_cost_usd': 0.0,
        'total_llm_requests': 0,
        'total_search_requests': 0,
        'total_input_tokens': 0,
        'total_output_tokens': 0,
        'total_tokens': 0,
        'model_breakdown': {},
        'provider_breakdown': {}
    },
    'last_updated': datetime.now().isoformat()
}

# Lưu vào file
file_path = Path('data/research_tasks/7c6867f0-b822-4317-ae57-b0f4942312c3/cost.json')
with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(cost_data, f, ensure_ascii=False, indent=2)

print(f'Đã tạo file {file_path}') 