# 📚 文档中心

欢迎来到DL-WAF文档中心。请按照以下指南查找相关文档。

## 🎯 按使用场景快速查找

### 👤 我是新用户
1. 先读 [../../START_HERE.md](../../START_HERE.md) (5分钟)
2. 再读 [guides/QUICKSTART.md](guides/QUICKSTART.md) (15分钟)
3. 尝试运行 `python main.py`

### 👨‍💻 我是开发者
1. 阅读 [architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md) - 了解系统设计
2. 查看 [guides/API_REFERENCE.md](guides/API_REFERENCE.md) - API文档
3. 学习 [guides/USAGE_GUIDE.md](guides/USAGE_GUIDE.md) - 详细操作指南

### 🔐 我想添加新规则
1. 查看 `../../rules/` 目录中的YAML样例
2. 参考 [guides/USAGE_GUIDE.md](guides/USAGE_GUIDE.md) 中的"规则编写"部分
3. 在 `config/settings.yaml` 中配置规则路径

### 📊 我想了解系统性能
1. 查看 [reports/SYSTEM_HEALTH_ASSESSMENT.md](reports/SYSTEM_HEALTH_ASSESSMENT.md)
2. 查看 [reports/ROBUSTNESS_TEST_REPORT.md](reports/ROBUSTNESS_TEST_REPORT.md)
3. 查看 [reports/TEST_AND_ASSESSMENT_SUMMARY.md](reports/TEST_AND_ASSESSMENT_SUMMARY.md)

### 🛠️ 我想改进系统
1. 查看 [reports/SYSTEM_IMPROVEMENT_PLAN.md](reports/SYSTEM_IMPROVEMENT_PLAN.md)
2. 参考源代码中的 `docstring` 注释
3. 运行测试确认改动无误

## 📁 文档目录结构

```
docs/
├── guides/                           # 📖 使用指南
│   ├── QUICKSTART.md                # 快速开始（15分钟）
│   ├── USAGE_GUIDE.md               # 详细使用指南
│   └── API_REFERENCE.md             # API参考文档
│
├── reports/                          # 📊 技术报告
│   ├── ROBUSTNESS_TEST_REPORT.md    # 鲁棒性测试报告
│   ├── SYSTEM_HEALTH_ASSESSMENT.md  # 系统健康评估
│   ├── SYSTEM_IMPROVEMENT_PLAN.md   # 改进计划
│   └── TEST_AND_ASSESSMENT_SUMMARY.md  # 汇总报告
│
└── architecture/                     # 🏗️ 架构文档
    ├── ARCHITECTURE.md              # 系统架构设计
    └── COMPONENT_DESIGN.md          # 组件设计详解
```

## 📖 文档列表

### 指南类
| 文档 | 时间 | 内容 |
|------|------|------|
| [QUICKSTART.md](guides/QUICKSTART.md) | 15分钟 | 快速上手，基本操作 |
| [USAGE_GUIDE.md](guides/USAGE_GUIDE.md) | 30分钟 | 详细功能说明，高级用法 |
| [API_REFERENCE.md](guides/API_REFERENCE.md) | 参考 | API端点、请求/响应格式 |

### 报告类
| 文档 | 用途 | 受众 |
|------|------|------|
| [ROBUSTNESS_TEST_REPORT.md](reports/ROBUSTNESS_TEST_REPORT.md) | 测试验证 | QA/开发者 |
| [SYSTEM_HEALTH_ASSESSMENT.md](reports/SYSTEM_HEALTH_ASSESSMENT.md) | 性能评估 | 架构师/管理者 |
| [SYSTEM_IMPROVEMENT_PLAN.md](reports/SYSTEM_IMPROVEMENT_PLAN.md) | 改进计划 | 开发团队 |
| [TEST_AND_ASSESSMENT_SUMMARY.md](reports/TEST_AND_ASSESSMENT_SUMMARY.md) | 整体总结 | 所有人 |

### 架构类
| 文档 | 主题 | 深度 |
|------|------|------|
| [ARCHITECTURE.md](architecture/ARCHITECTURE.md) | 系统设计 | 深度 |
| [COMPONENT_DESIGN.md](architecture/COMPONENT_DESIGN.md) | 组件设计 | 深度 |

## 🔗 导航提示

- **回到项目根目录**: [../../](../../)
- **查看项目结构**: [../../PROJECT_STRUCTURE.md](../../PROJECT_STRUCTURE.md)
- **源代码位置**: [../../src/](../../src/)
- **规则库位置**: [../../rules/](../../rules/)

## ❓ 常见问题

**Q: 文档太多，从哪里开始？**  
A: 新用户建议按此顺序: START_HERE → QUICKSTART → USAGE_GUIDE

**Q: 我只想快速演示系统？**  
A: 运行 `python main.py`，访问 http://localhost:5000

**Q: 系统性能如何？**  
A: 查看 SYSTEM_HEALTH_ASSESSMENT.md，总体评分 9.6/10

**Q: 如何部署到生产环境？**  
A: 查看 SYSTEM_IMPROVEMENT_PLAN.md 的部署章节

---

**最后更新**: 2026年1月29日  
**文档版本**: 1.0.0  
**系统版本**: 1.0.0
