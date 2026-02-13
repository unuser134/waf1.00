# FILE ORGANIZATION

项目文件组织说明（简要）：

- `main.py` - 系统入口
- `src/` - 源代码
- `rules/` - WAF 规则 YAML
- `config/` - 配置文件
- `docs/` - 项目文档
- `models/` - 训练与保存的模型
- `logs/` - 运行时日志

开发者指南：

- 阅读 `src/core/` 了解检测逻辑
- 阅读 `src/web/` 了解 Web 管理界面
- 运行 `python -m pytest` 运行测试

更多细节请查看 docs/02_core_features/ 和 docs/03_testing/。