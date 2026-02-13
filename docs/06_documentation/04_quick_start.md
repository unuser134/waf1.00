# ⚡ 快速开始指南 (15分钟)

## 📋 目标

在15分钟内启动并演示DL-WAF系统。

## 🚀 安装 (3分钟)

### 前置要求
- Python 3.8+
- pip 或 conda

### 安装步骤

```bash
# 1. 进入项目目录
cd dl-waf-hybrid

# 2. 创建虚拟环境（可选但推荐）
python -m venv venv

# 3. 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. 安装依赖
pip install -r requirements.txt
```

## ▶️ 启动系统 (2分钟)

### 方法一：完整系统（推荐）

```bash
# 启动系统
python main.py

# 输出示例：
# [INFO] Loading rules from rules/
# [INFO] Rule Engine initialized: 14 rules loaded
# [INFO] Starting WAF Web Application...
# * Running on http://localhost:5000
```

然后打开浏览器访问：**http://localhost:5000**

### 方法二：仅运行规则引擎

```bash
python -c "from src.core.rule_engine import RuleEngine; 
engine = RuleEngine(); 
print(f'Loaded {len(engine.rules)} rules')"
```

### 方法三：运行功能演示

```bash
python feature_demo.py
```

## 🎯 快速体验 (10分钟)

### 场景1：测试SQL注入检测

**Web界面方式**：
1. 访问 http://localhost:5000
2. 在"Test Attack"输入框中输入：`SELECT * FROM users OR 1=1`
3. 点击"Send Request"
4. 查看仪表板中的"Attack Statistics"

**API方式**：
```bash
curl -X POST http://localhost:5000/api/detect \
  -H "Content-Type: application/json" \
  -d '{"url": "http://example.com", "body": "SELECT * FROM users OR 1=1"}'

# 响应示例：
# {"attack": true, "block": true, "matches": [{"rule": "SQL_OR_1_1"}]}
```

### 场景2：测试XSS检测

```bash
curl -X POST http://localhost:5000/api/detect \
  -H "Content-Type: application/json" \
  -d '{"url": "http://example.com", "body": "<img src=x onerror=alert(1)>"}'

# 响应：{"attack": true, "block": true, "matches": [...]}
```

### 场景3：查看攻击日志

```bash
curl http://localhost:5000/api/logs?limit=10

# 返回最近10条攻击日志
```

## 📊 查看仪表板

访问 http://localhost:5000 后，你会看到：

- **Attack Statistics** - 按类型、严重程度分类的攻击统计
- **Real-time Logs** - 实时攻击日志
- **Performance Metrics** - 检测性能指标
- **Whitelist Management** - IP/URL白名单管理

## 🧪 运行测试 (可选)

### 运行所有测试
```bash
# 完整的鲁棒性测试 (35个测试)
python src/tests/robustness_test.py

# 集成测试 (22个测试)
python src/tests/test_integration.py
```

### 预期结果
```
总测试项: 35
通过: 35
失败: 0
成功率: 100.0%
```

## 📝 基本操作

### 添加IP白名单

```bash
curl -X POST http://localhost:5000/api/whitelist \
  -H "Content-Type: application/json" \
  -d '{"type": "ip", "value": "192.168.1.100"}'
```

### 获取统计数据

```bash
curl "http://localhost:5000/api/stats?hours=24"

# 返回包含以下字段的统计数据：
# - total_attacks: 总攻击数
# - by_category: 按攻击类型分类
# - by_severity: 按严重程度分类
# - by_rule: 按规则分类（新增）
# - top_attacked_urls: 最频繁被攻击的URL（新增）
# - top_attackers: 最频繁的攻击源IP（新增）
```

### 热重载规则

```bash
curl -X POST http://localhost:5000/api/rules/reload

# 响应：{"status": "success", "message": "Rules reloaded"}
```

## 🛑 停止系统

```bash
# 在运行main.py的终端中按 Ctrl+C
```

## 📚 后续学习

- **详细指南**: 阅读 [USAGE_GUIDE.md](USAGE_GUIDE.md)
- **API文档**: 查看 [API_REFERENCE.md](API_REFERENCE.md)
- **系统设计**: 阅读 [../architecture/ARCHITECTURE.md](../architecture/ARCHITECTURE.md)
- **添加规则**: 参考 `rules/` 目录中的YAML文件

## ✅ 检查清单

- [ ] Python 3.8+ 已安装
- [ ] 依赖包已安装 (`pip install -r requirements.txt`)
- [ ] `python main.py` 成功启动
- [ ] 浏览器访问 http://localhost:5000 显示仪表板
- [ ] 能够通过API发送测试请求
- [ ] 日志中显示检测结果

## ❓ 故障排除

### 问题：ModuleNotFoundError
**解决**: 确认已安装依赖
```bash
pip install -r requirements.txt
```

### 问题：Port 5000 already in use
**解决**: 修改 `src/web/app.py` 中的端口号或杀死占用进程

### 问题：Rules not loading
**解决**: 检查 `config/settings.yaml` 中的规则路径配置

### 问题：Unicode characters display incorrectly
**解决**: 设置环境变量（Windows）
```bash
set PYTHONIOENCODING=utf-8
```

---

**预计时间**: 15分钟 ⏱️  
**难度**: ⭐ 简单  
**下一步**: 阅读 [USAGE_GUIDE.md](USAGE_GUIDE.md)
