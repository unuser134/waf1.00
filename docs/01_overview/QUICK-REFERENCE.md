# QUICK REFERENCE

常用命令与快速参考：

- 启动服务: `python main.py`
- 运行测试: `python -m pytest`
- 更新规则: 编辑 `rules/*.yaml`，然后在 Web UI 中点击 `规则 -> 重新加载`
- 导出日志: 在 Web UI 的 `日志` 页面选择导出为 CSV

配置文件位置：

- `config/settings.yaml` - 运行时设置
- `config/whitelist.yaml` - 白名单配置

日志与监控：

- 日志文件夹: `logs/`
- Web 管理: http://localhost:8082

错误排查：

- 检查 `logs/` 中最新日志
- 查看 `main.py` 输出的异常信息

更多细节请查看 docs/ 目录下相应文档。