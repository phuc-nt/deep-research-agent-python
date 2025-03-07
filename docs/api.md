# Deep Research Agent API

API cho hệ thống nghiên cứu tự động sử dụng AI.

## Base URL

```
http://localhost:8000/api/v1
```

## Endpoints

### Tạo yêu cầu nghiên cứu mới

```
POST /research
```

#### Request Body

```json
{
  "query": "Nghiên cứu về trí tuệ nhân tạo và ứng dụng trong giáo dục",
  "topic": "Trí tuệ nhân tạo trong giáo dục",
  "scope": "Tổng quan và ứng dụng thực tế",
  "target_audience": "Giáo viên và nhà quản lý giáo dục"
}
```

| Tham số | Kiểu | Mô tả |
|---------|------|-------|
| query | string | Yêu cầu nghiên cứu (bắt buộc) |
| topic | string | Chủ đề nghiên cứu (tùy chọn) |
| scope | string | Phạm vi nghiên cứu (tùy chọn) |
| target_audience | string | Đối tượng độc giả (tùy chọn) |

#### Response

```json
{
  "id": "ca214ee5-6204-4f3d-98c4-4f558e27399b",
  "status": "pending",
  "request": {
    "query": "Nghiên cứu về trí tuệ nhân tạo và ứng dụng trong giáo dục",
    "topic": "Trí tuệ nhân tạo trong giáo dục",
    "scope": "Tổng quan và ứng dụng thực tế",
    "target_audience": "Giáo viên và nhà quản lý giáo dục"
  },
  "outline": null,
  "result": null,
  "error": null,
  "github_url": null,
  "created_at": "2023-03-11T10:15:30.123456",
  "updated_at": "2023-03-11T10:15:30.123456"
}
```

### Lấy thông tin và kết quả nghiên cứu

```
GET /research/{research_id}
```

#### Path Parameters

| Tham số | Kiểu | Mô tả |
|---------|------|-------|
| research_id | string | ID của research task |

#### Response

```json
{
  "id": "ca214ee5-6204-4f3d-98c4-4f558e27399b",
  "status": "completed",
  "request": {
    "query": "Nghiên cứu về trí tuệ nhân tạo và ứng dụng trong giáo dục",
    "topic": "Trí tuệ nhân tạo trong giáo dục",
    "scope": "Tổng quan và ứng dụng thực tế",
    "target_audience": "Giáo viên và nhà quản lý giáo dục"
  },
  "outline": {
    "sections": [
      {
        "title": "Giới thiệu về trí tuệ nhân tạo trong giáo dục",
        "description": "Tổng quan về AI và vai trò trong lĩnh vực giáo dục",
        "content": "..."
      },
      {
        "title": "Các ứng dụng hiện tại của AI trong giáo dục",
        "description": "Các ứng dụng đã và đang được triển khai",
        "content": "..."
      }
    ]
  },
  "result": {
    "title": "Trí tuệ nhân tạo trong giáo dục: Hiện tại và tương lai",
    "content": "...",
    "sections": [...],
    "sources": [
      "https://example.com/source1",
      "https://example.com/source2"
    ]
  },
  "error": null,
  "github_url": "https://github.com/username/repo/research-123",
  "created_at": "2023-03-11T10:15:30.123456",
  "updated_at": "2023-03-11T10:20:45.678901"
}
```

### Lấy trạng thái nghiên cứu

```
GET /research/{research_id}/status
```

#### Path Parameters

| Tham số | Kiểu | Mô tả |
|---------|------|-------|
| research_id | string | ID của research task |

#### Response

```
"completed"
```

Các trạng thái có thể:
- `pending`: Đang chờ xử lý
- `analyzing`: Đang phân tích yêu cầu
- `outlining`: Đang tạo dàn ý
- `researching`: Đang nghiên cứu
- `editing`: Đang chỉnh sửa
- `completed`: Đã hoàn thành
- `failed`: Thất bại

### Lấy dàn ý nghiên cứu

```
GET /research/{research_id}/outline
```

#### Path Parameters

| Tham số | Kiểu | Mô tả |
|---------|------|-------|
| research_id | string | ID của research task |

#### Response

```json
{
  "sections": [
    {
      "title": "Giới thiệu về trí tuệ nhân tạo trong giáo dục",
      "description": "Tổng quan về AI và vai trò trong lĩnh vực giáo dục",
      "content": null
    },
    {
      "title": "Các ứng dụng hiện tại của AI trong giáo dục",
      "description": "Các ứng dụng đã và đang được triển khai",
      "content": null
    }
  ]
}
```

## Quy trình nghiên cứu

1. **Tạo yêu cầu nghiên cứu**: Gửi POST request đến `/research` với thông tin yêu cầu
2. **Theo dõi tiến độ**: Gọi GET `/research/{research_id}/status` để kiểm tra trạng thái
3. **Xem dàn ý**: Khi trạng thái là `outlining` hoặc sau đó, có thể gọi GET `/research/{research_id}/outline` để xem dàn ý
4. **Lấy kết quả**: Khi trạng thái là `completed`, gọi GET `/research/{research_id}` để lấy kết quả đầy đủ

## Xử lý lỗi

Nếu có lỗi xảy ra trong quá trình nghiên cứu, trạng thái sẽ chuyển thành `failed` và thông tin lỗi sẽ được trả về trong trường `error`:

```json
{
  "id": "ca214ee5-6204-4f3d-98c4-4f558e27399b",
  "status": "failed",
  "request": {...},
  "outline": null,
  "result": null,
  "error": {
    "message": "Lỗi trong quá trình chuẩn bị",
    "details": {
      "error": "Lỗi khi phân tích yêu cầu nghiên cứu"
    }
  },
  "github_url": null,
  "created_at": "2023-03-11T10:15:30.123456",
  "updated_at": "2023-03-11T10:16:45.678901"
}
```

## Ví dụ sử dụng (Python)

```python
import requests
import time

BASE_URL = "http://localhost:8000/api/v1"

# Tạo yêu cầu nghiên cứu
data = {
    "query": "Nghiên cứu về trí tuệ nhân tạo và ứng dụng trong giáo dục",
    "topic": "Trí tuệ nhân tạo trong giáo dục",
    "scope": "Tổng quan và ứng dụng thực tế",
    "target_audience": "Giáo viên và nhà quản lý giáo dục"
}
response = requests.post(f"{BASE_URL}/research", json=data)
research_id = response.json()["id"]

# Theo dõi tiến độ
while True:
    status_response = requests.get(f"{BASE_URL}/research/{research_id}/status")
    status = status_response.json()
    
    print(f"Status: {status}")
    
    if status == "completed":
        # Lấy kết quả
        result_response = requests.get(f"{BASE_URL}/research/{research_id}")
        result = result_response.json()
        print("Research completed!")
        print(f"Title: {result['result']['title']}")
        print(f"Content length: {len(result['result']['content'])}")
        break
    elif status == "failed":
        # Xử lý lỗi
        error_response = requests.get(f"{BASE_URL}/research/{research_id}")
        error = error_response.json()["error"]
        print(f"Research failed: {error['message']}")
        break
    
    # Đợi 5 giây trước khi kiểm tra lại
    time.sleep(5)
```
