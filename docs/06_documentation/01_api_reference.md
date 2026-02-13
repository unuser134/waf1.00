# 📡 API 参考文档

## 📍 API基础信息

**基础URL**: `http://localhost:5000`  
**内容类型**: `application/json`  
**认证**: 无（当前版本）

## 🔍 API端点列表

| 方法 | 端点 | 说明 | 状态 |
|------|------|------|------|
| POST | `/api/detect` | 检测单个请求 | ✅ 稳定 |
| GET | `/api/logs` | 获取攻击日志 | ✅ 稳定 |
| GET | `/api/stats` | 获取统计数据 | ✅ 稳定 |
| GET | `/api/whitelist` | 获取白名单 | ✅ 稳定 |
| POST | `/api/whitelist` | 添加白名单 | ✅ 稳定 |
| DELETE | `/api/whitelist` | 删除白名单 | ✅ 稳定 |
| GET | `/api/rules` | 获取所有规则 | ✅ 稳定 |
| POST | `/api/rules/reload` | 热重载规则 | ✅ 稳定 |
| GET | `/` | Web仪表板 | ✅ 稳定 |

---

## 📨 API详细说明

### 1️⃣ 检测请求

#### POST /api/detect

检测单个HTTP请求是否包含攻击。

**请求体示例**:
```json
{
  "url": "http://example.com/search?q=SELECT * FROM users",
  "body": "username=admin&password=1' OR '1'='1",
  "method": "POST",
  "headers": {
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "Mozilla/5.0"
  }
}
```

**请求体字段说明**:

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| url | string | ✅ | 请求URL |
| body | string | ❌ | 请求体内容 |
| method | string | ❌ | HTTP方法 (GET/POST等) |
| headers | object | ❌ | 请求头字典 |

**成功响应 (200)**:
```json
{
  "attack": true,
  "block": true,
  "source": "rule_engine",
  "rule_name": "SQL_OR_1_1",
  "category": "sql_injection",
  "severity": "critical",
  "confidence": 1.0,
  "matches": [
    {
      "rule_name": "SQL_OR_1_1",
      "pattern": "(?i)or\\s+1\\s*=\\s*1",
      "category": "sql_injection",
      "severity": "critical",
      "priority": 3,
      "confidence": 0.99
    }
  ]
}
```

**响应字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| attack | boolean | 是否被检测为攻击 |
| block | boolean | 是否应被阻止 |
| source | string | 检测来源 (rule_engine/dl_detector/hybrid) |
| rule_name | string | 触发的规则名称 |
| category | string | 攻击类别 (sql_injection/xss等) |
| severity | string | 严重程度 (critical/high/medium/low) |
| confidence | float | 置信度 (0.0-1.0) |
| matches | array | 匹配的规则列表 |

**cURL 示例**:
```bash
curl -X POST http://localhost:5000/api/detect \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://example.com/search",
    "body": "SELECT * FROM users WHERE id=1 OR 1=1"
  }'
```

**Python 示例**:
```python
import requests

response = requests.post(
    'http://localhost:5000/api/detect',
    json={
        'url': 'http://example.com/search',
        'body': 'SELECT * FROM users WHERE id=1 OR 1=1'
    }
)
print(response.json())
```

---

### 2️⃣ 查询日志

#### GET /api/logs

获取攻击日志，支持过滤和分页。

**查询参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| limit | int | 100 | 返回记录数 (1-10000) |
| offset | int | 0 | 分页偏移 |
| filter_type | string | 无 | 过滤攻击类型 (sql_injection/xss等) |
| filter_severity | string | 无 | 过滤严重程度 (critical/high等) |

**请求示例**:
```bash
# 获取最近100条日志
GET /api/logs

# 获取最近10条SQL注入攻击
GET /api/logs?limit=10&filter_type=sql_injection

# 获取严重程度为critical的日志，从第20条开始
GET /api/logs?limit=50&offset=20&filter_severity=critical
```

**成功响应 (200)**:
```json
{
  "total": 256,
  "logs": [
    {
      "timestamp": "2026-01-29T14:32:45.123456",
      "category": "sql_injection",
      "severity": "critical",
      "rule_name": "SQL_OR_1_1",
      "request_body": "SELECT * FROM users WHERE id=1 OR 1=1",
      "source_ip": "192.168.1.100",
      "target_url": "http://example.com/search",
      "blocked": true
    },
    {
      "timestamp": "2026-01-29T14:30:12.654321",
      "category": "xss",
      "severity": "high",
      "rule_name": "XSS_SCRIPT_TAG",
      "request_body": "<script>alert(1)</script>",
      "source_ip": "192.168.1.101",
      "target_url": "http://example.com/comment",
      "blocked": true
    }
  ]
}
```

**Python 示例**:
```python
import requests

response = requests.get(
    'http://localhost:5000/api/logs',
    params={
        'limit': 10,
        'filter_type': 'sql_injection'
    }
)
logs = response.json()['logs']
for log in logs:
    print(f"{log['timestamp']} - {log['category']} - {log['rule_name']}")
```

---

### 3️⃣ 获取统计数据

#### GET /api/stats

获取攻击统计数据（支持多维统计）。

**查询参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| hours | int | 24 | 统计时间范围（小时） |

**请求示例**:
```bash
# 获取最近24小时统计
GET /api/stats

# 获取最近1小时统计
GET /api/stats?hours=1

# 获取最近7天统计
GET /api/stats?hours=168
```

**成功响应 (200)**:
```json
{
  "total_attacks": 156,
  "by_category": {
    "sql_injection": 45,
    "xss": 52,
    "directory_traversal": 35,
    "malicious_file": 24
  },
  "by_severity": {
    "critical": 65,
    "high": 65,
    "medium": 20,
    "low": 6
  },
  "by_rule": {
    "SQL_OR_1_1": 28,
    "SQL_UNION": 12,
    "XSS_SCRIPT_TAG": 32,
    "XSS_EVENT_HANDLER": 18,
    "DIR_TRAVERSAL_UNIX": 22,
    "FILE_INCLUSION": 13,
    "EXE_UPLOAD": 15,
    "SHELL_UPLOAD": 9
  },
  "top_attacked_urls": [
    {"url": "/api/search", "count": 34},
    {"url": "/api/comment", "count": 28},
    {"url": "/api/upload", "count": 22},
    {"url": "/api/profile", "count": 18},
    {"url": "/api/download", "count": 12}
  ],
  "top_attackers": [
    {"source_ip": "192.168.1.100", "count": 45},
    {"source_ip": "192.168.1.101", "count": 38},
    {"source_ip": "192.168.1.102", "count": 32},
    {"source_ip": "192.168.1.103", "count": 25},
    {"source_ip": "192.168.1.104", "count": 16}
  ],
  "hourly_trend": {
    "2026-01-29 14:00": 12,
    "2026-01-29 13:00": 18,
    "2026-01-29 12:00": 15,
    "2026-01-29 11:00": 9
  }
}
```

**新增字段说明** ✨:

| 字段 | 说明 |
|------|------|
| by_rule | 按触发规则统计，便于识别最常被触发的规则 |
| top_attacked_urls | Top 5最频繁被攻击的URL，用于优化防护 |
| top_attackers | Top 5最频繁的攻击源IP，便于追踪 |

---

### 4️⃣ 白名单管理

#### GET /api/whitelist

获取所有白名单条目。

**请求示例**:
```bash
GET /api/whitelist
```

**成功响应 (200)**:
```json
{
  "ips": [
    "192.168.1.0/24",
    "10.0.0.0/8"
  ],
  "urls": [
    "/api/health",
    "/status"
  ],
  "total": 4
}
```

---

#### POST /api/whitelist

添加白名单条目。

**请求体示例** (3种格式支持):

```json
{
  "type": "ip",
  "value": "192.168.1.100"
}
```

或

```json
{
  "type": "url",
  "value": "/api/health"
}
```

或

```json
{
  "type": "pattern",
  "value": "(?i)^/admin/.*"
}
```

**请求体字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 类型 (ip/url/pattern) |
| value | string | 值 (IP地址/URL/正则表达式) |

**成功响应 (200)**:
```json
{
  "status": "success",
  "message": "Whitelist entry added successfully",
  "entry": {
    "type": "ip",
    "value": "192.168.1.100"
  }
}
```

**cURL 示例**:
```bash
curl -X POST http://localhost:5000/api/whitelist \
  -H "Content-Type: application/json" \
  -d '{
    "type": "ip",
    "value": "192.168.1.100"
  }'
```

---

#### DELETE /api/whitelist

删除白名单条目。

**查询参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| type | string | 类型 (ip/url/pattern) |
| value | string | 值 |

**请求示例**:
```bash
DELETE /api/whitelist?type=ip&value=192.168.1.100
```

**成功响应 (200)**:
```json
{
  "status": "success",
  "message": "Whitelist entry removed successfully"
}
```

---

### 5️⃣ 规则管理

#### GET /api/rules

获取所有WAF规则。

**请求示例**:
```bash
GET /api/rules
```

**成功响应 (200)**:
```json
{
  "total": 14,
  "rules": [
    {
      "name": "SQL_OR_1_1",
      "category": "sql_injection",
      "severity": "critical",
      "enabled": true,
      "priority": 3,
      "confidence": 0.99,
      "pattern_count": 1,
      "patterns": [
        "(?i)or\\s+1\\s*=\\s*1"
      ]
    },
    {
      "name": "XSS_SCRIPT_TAG",
      "category": "xss",
      "severity": "critical",
      "enabled": true,
      "priority": 5,
      "confidence": 0.98,
      "pattern_count": 2,
      "patterns": [
        "<script[^>]*>",
        "</script>"
      ]
    }
  ]
}
```

---

#### POST /api/rules/reload

热重载所有规则（无需重启系统）。

**请求示例**:
```bash
POST /api/rules/reload
```

**成功响应 (200)**:
```json
{
  "status": "success",
  "message": "Rules reloaded successfully",
  "rules_loaded": 14,
  "timestamp": "2026-01-29T14:35:22.123456"
}
```

---

### 6️⃣ 仪表板

#### GET /

返回Web管理仪表板HTML页面。

**请求示例**:
```bash
GET http://localhost:5000
```

**浏览器访问**: 直接访问 http://localhost:5000

---

## 🎯 常见使用场景

### 场景1: 批量检测多个请求

```python
import requests

requests_to_check = [
    {"url": "http://example.com/search", "body": "SELECT * FROM users"},
    {"url": "http://example.com/comment", "body": "<script>alert(1)</script>"},
    {"url": "http://example.com/download", "body": "../../etc/passwd"}
]

for req in requests_to_check:
    response = requests.post('http://localhost:5000/api/detect', json=req)
    result = response.json()
    
    if result['block']:
        print(f"⚠️ 阻止 - {result['category']}: {result['rule_name']}")
    else:
        print(f"✅ 放行 - {req['url']}")
```

### 场景2: 实时监控攻击趋势

```python
import requests
import time

while True:
    stats = requests.get('http://localhost:5000/api/stats?hours=1').json()
    
    print(f"过去1小时: {stats['total_attacks']} 次攻击")
    print(f"按类型: {stats['by_category']}")
    print(f"最频繁的攻击源: {stats['top_attackers'][0]['source_ip']}")
    
    time.sleep(300)  # 每5分钟刷新
```

### 场景3: 管理白名单

```python
import requests

# 添加内部网络到白名单
requests.post(
    'http://localhost:5000/api/whitelist',
    json={"type": "ip", "value": "192.168.1.0/24"}
)

# 添加健康检查端点
requests.post(
    'http://localhost:5000/api/whitelist',
    json={"type": "url", "value": "/health"}
)

# 查看所有白名单
whitelist = requests.get('http://localhost:5000/api/whitelist').json()
print(f"白名单IP数: {len(whitelist['ips'])}")
```

---

## ⚠️ 错误响应

### 400 Bad Request
```json
{
  "error": "Missing required field: url",
  "status": 400
}
```

### 404 Not Found
```json
{
  "error": "API endpoint not found",
  "status": 404
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "details": "..."
}
```

---

## 📊 响应时间参考

| 操作 | 响应时间 | 备注 |
|------|---------|------|
| 检测单个请求 | 0.08ms | 平均值，含规则+DL |
| 查询100条日志 | 5-10ms | 取决于日志量 |
| 获取统计数据 | 2-5ms | 实时计算 |
| 添加白名单 | 1ms | 内存操作 |
| 热重载规则 | 7.45ms | 编译正则表达式 |

---

## 🔐 安全建议

1. **生产环境** - 建议添加身份验证中间件
2. **速率限制** - 建议实施API速率限制
3. **日志审计** - 定期审查白名单变更
4. **HTTPS** - 生产环境建议使用HTTPS
5. **备份** - 定期备份规则和白名单配置

---

**API版本**: 1.0.0  
**最后更新**: 2026年1月29日

