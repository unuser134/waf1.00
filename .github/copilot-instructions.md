# 🛡️ DL混合WAF系统 - Copilot开发指南

本文档指导AI coding agents高效地在DL-WAF项目中工作。

## 🎯 项目核心概念

**DL混合WAF (Deep Learning Hybrid Web Application Firewall)** 是一个结合规则匹配和深度学习的安全检测系统。核心特点：

- **混合检测架构**: 规则引擎 + DL模型的融合决策，而非单一方案
- **快速精确匹配**: 规则引擎处理已知攻击（SQL、XSS等）
- **未知攻击识别**: 深度学习模型在规则无法覆盖时提供防护
- **实时监控**: Web管理界面展示攻击统计和系统状态

## 📂 关键文件结构与职责

```
src/core/
├── rule_engine.py          # 规则匹配引擎（关键）
└── dl_detector.py          # DL检测模型（关键）

src/web/
├── app.py                  # Flask Web应用（关键）
└── templates/dashboard.html # 管理仪表板（关键）

rules/                       # WAF规则库（易修改）
├── sql_injection.yaml
├── xss.yaml
├── directory_traversal.yaml
└── malicious_file.yaml

main.py                      # 系统入口与集成（关键）
```

**关键文件** = 系统架构核心，修改前需理解设计意图  
**易修改文件** = 规则和配置，可灵活扩展

## 🏗️ 架构决策和为什么

### 1. 规则引擎为什么采用YAML？
- **易维护**: 安全人员可直接编写和修改规则，无需编程
- **快速扩展**: 新增攻击类型时只需添加YAML文件
- **配置集中**: 所有规则配置在一处，版本控制友好

### 2. 为什么需要DL模型？
- **规则局限性**: 已知规则无法覆盖所有变种和零日攻击
- **自适应学习**: 模型可从新数据中学习未知攻击模式
- **融合优势**: 规则快速精确，DL覆盖深度，互补不冲突

### 3. 融合决策为什么这样设计？
```python
# src/main.py 中的detect_request方法
rule_triggered or (is_attack and dl_confidence > 0.7)
```
- 规则优先: 规则触发立即阻止（精准度最高）
- DL门槛: 0.7置信度避免假正例过多
- 保守策略: 两个系统中任一高度确信就阻止

## 💼 常见开发任务

### 添加新的WAF规则

**任务**: 添加对新攻击类型（如LDAP注入）的检测

**步骤**:
1. 创建 `rules/ldap_injection.yaml`（参考sql_injection.yaml的格式）
2. 在 `config/settings.yaml` 的rules.directories中添加路径
3. 无需修改Python代码，系统自动加载

**相关代码** (src/core/rule_engine.py):
```python
def load_rules(self):
    """从YAML文件加载所有规则"""
    for rule_file in self.rule_files:
        # YAML加载逻辑
```

### 改进DL模型

**任务**: 提高模型对特定攻击类型的识别率

**步骤**:
1. 在 `data/raw/` 放置新的训练数据（HTTP请求 + 标签）
2. 编写数据加载器并调用 `detector.train()`（参考src/tests/test_system.py）
3. 模型自动保存到 `models/saved/dl_model.pth`
4. 系统下次启动自动加载新模型

**相关代码** (src/core/dl_detector.py):
```python
def predict(self, request_text: str, threshold: float = 0.5):
    """推理接口 - 改进模型后这里自动使用新权重"""
```

### 扩展Web管理界面

**任务**: 添加新的监控指标或管理功能

**关键点**:
- **后端**: src/web/app.py 中添加新API端点
- **前端**: src/web/templates/dashboard.html 中添加新的HTML/JS代码
- **数据流**: API返回JSON → JS解析 → 动态更新DOM

**示例** (添加新统计指标):
```python
# src/web/app.py
@self.app.route('/api/custom-stats', methods=['GET'])
def custom_stats():
    return jsonify({'custom_data': ...})

# dashboard.html 中调用
fetch('/api/custom-stats').then(r => r.json()).then(data => {...})
```

## 🔧 核心对象与关键方法

### RuleEngine (规则匹配)

**关键方法**:
- `detect(request_data)` → (是否触发规则, 匹配规则列表)
- `load_rules()` → 从YAML加载规则到内存
- `reload_rules()` → 热重载规则（无需重启）
- `get_stats()` → 规则统计信息

**使用场景**:
```python
engine = RuleEngine()
is_attack, matches = engine.detect({
    'url': request.url,
    'body': request.data,
    'headers': dict(request.headers)
})
```

### DLDetector (深度学习)

**关键方法**:
- `predict(request_text)` → (是否为攻击, 置信度, 详情)
- `train(train_loader, val_loader, epochs)` → 训练模型
- `save_model()` → 保存权重到models/saved/dl_model.pth
- `load_model()` → 加载已训练的权重

**特征提取**:
```python
# src/core/dl_detector.py - FeatureExtractor类
# 256维特征向量 = 字符统计 + 特殊字符 + 频率分布
features = feature_extractor.extract_features(request_text)
```

**模型架构**:
```
输入(256维) → FC层(128) → ReLU → 
           → FC层(64)  → ReLU → 
           → FC层(32)  → ReLU → 
           → FC层(2)   → Softmax
输出: [P(正常), P(攻击)]
```

### WAFWebApp (Web管理)

**关键API**:
- `/api/stats` - 时间范围内的攻击统计
- `/api/logs` - 攻击日志查询和过滤
- `/api/whitelist` - 白名单CRUD
- `/api/rules/reload` - 规则热重载

**日志管理** (AttackLog类):
```python
# 内存缓存实现，最多保存10000条
attack_log.add_log({'category': 'sql_injection', 'severity': 'high'})
logs = attack_log.get_logs(limit=100, filter_type='sql_injection')
stats = attack_log.get_stats(hours=24)
```

## 📊 数据流和集成点

### 端到端流程

```
1. HTTP请求到达
   ↓
2. RuleEngine.detect(request) 
   → 快速正则匹配，返回规则触发情况
   ↓
3. DLDetector.predict(request_text)
   → 特征提取 → 神经网络推理 → 攻击置信度
   ↓
4. main.py 中的融合决策
   → if rule_triggered or (dl_attack and confidence > 0.7): BLOCK
   ↓
5. WAFWebApp.add_log(decision)
   → 日志记录到AttackLog
   ↓
6. Web界面实时展示
   → 前端定时GET /api/logs → 表格更新
```

### 关键集成点

**main.py**:
```python
class WAFSystem:
    def detect_request(self, request_data):
        # 集成规则引擎和DL检测器的决策融合点
        rule_triggered, _ = self.rule_engine.detect(request_data)
        is_attack, confidence, _ = self.dl_detector.predict(request_text)
        should_block = rule_triggered or (is_attack and confidence > 0.7)
```

## 🎨 代码规范和模式

### 规则文件格式 (rules/*.yaml)

```yaml
rules:
  - name: "ATTACK_TYPE_DESCRIPTION"      # 唯一标识
    category: "sql_injection"             # 攻击类别
    severity: "critical|high|medium|low"  # 严重程度
    enabled: true|false                   # 启用状态
    patterns:
      - "(?i)regex_pattern_1"             # 正则表达式（区分大小写）
      - "(?i)regex_pattern_2"
```

**最佳实践**:
- 使用 `(?i)` 进行不区分大小写匹配
- patterns列表中任一匹配即判定为规则触发
- severity影响日志和统计，但不影响阻止决策

### Python代码结构

**模块化设计**:
- `src/core/` - 核心检测逻辑，无依赖Flask
- `src/web/` - Web应用层，依赖Flask
- `src/utils/` - 辅助工具函数
- `src/tests/` - 测试和演示代码

**错误处理**:
```python
try:
    result = engine.detect(request)
except Exception as e:
    logger.error(f"检测失败: {e}")
    return False, []  # 检测失败时返回安全的默认值
```

## 🧪 测试和验证

### 验证规则

```bash
# 运行系统测试
python src/tests/test_system.py

# 输出包括：
# ✓ 规则引擎测试（各种攻击类型）
# ✓ DL检测器测试（特征提取和推理）
# ✓ 混合检测测试（融合决策）
```

### 手动测试新规则

```python
from src.core.rule_engine import RuleEngine

engine = RuleEngine()
test_payload = "你的攻击载荷"
is_attack, matches = engine.detect({'url': test_payload, 'body': '', 'method': 'GET'})
print(f"触发规则: {[m['rule_name'] for m in matches]}")
```

## ⚡ 性能考虑

### 规则引擎优化
- 规则按category分组，支持快速范围查询
- 正则表达式编译在加载时完成，推理时直接使用
- 匹配时逐规则检查，第一个匹配即返回

### DL检测器优化
- 特征提取限制文本长度为1000字符，避免超大输入
- 使用GPU加速（如果可用），通过 `device` 参数控制
- 模型使用批量推理时效率最高

### Web应用优化
- AttackLog使用内存缓存（maxlen=10000），自动淘汰旧日志
- API使用JSON格式，前端定时查询（间隔5秒）
- 白名单/黑名单使用Set数据结构，O(1)查询

## 📝 常见问题和解决方案

**Q: 如何调整检测的阈值？**  
A: 修改main.py中的 `should_block = ... and dl_confidence > 0.7` 的阈值

**Q: 规则加载失败怎么办？**  
A: 检查config/settings.yaml中rules.directories的路径和权限

**Q: DL模型为什么初始化失败？**  
A: 删除models/saved/dl_model.pth让系统重新初始化，或检查PyTorch版本

**Q: 如何扩展特征提取维度？**  
A: 修改DLDetector的feature_dim参数，重新训练模型

## 🎯 开发建议

1. **修改前先阅读**: 规则匹配、DL推理、Web集成的设计原理
2. **充分测试**: 每次修改后运行 `python src/tests/test_system.py`
3. **保持兼容性**: 新增功能应与现有架构兼容
4. **文档更新**: 修改后更新相关的文档和注释
5. **版本控制**: 模型weights单独管理，不提交到git

## 📞 文档参考

- 详细设计: `README_NEW.md`
- 快速参考: `QUICKSTART.md`
- 代码注释: 各源文件中的docstring

---

**版本**: 1.0.0 | **最后更新**: 2026年1月29日
