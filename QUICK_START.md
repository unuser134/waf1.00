# 🛡️ DL-WAF 1.0 - 5分钟快速启动指南

## ⚡ 最快方式（推荐）

### Windows 用户
1. **解压** `dist/waf-1.0-*.zip` 到任意目录
2. **双击** `start-waf.bat` 即可启动
3. **打开浏览器** http://localhost:8082

### Linux/macOS 用户
1. **解压** `dist/waf-1.0-*.zip` 到任意目录
   ```bash
   unzip dist/waf-1.0-*.zip
   cd waf-1.0
   ```

2. **运行启动脚本**
   ```bash
   bash start-waf.sh
   ```

3. **打开浏览器** http://localhost:8082

---

## ✨ 一键启动后的功能

### 📊 仪表板（自动打开）
- 实时攻击统计
- 规则触发统计
- 攻击分布饼图

### 📋 日志查询
- 查看所有攻击日志
- 按攻击类型过滤
- 导出为 JSON

### 🔒 规则管理
- 查看 14 条检测规则
- 启用/禁用规则
- 热重载规则

### ⚪ 白名单配置
- 添加 IP/URL 白名单
- 批量导入
- 实时生效

### 🚀 部署配置
- 选择运行模式（保护/检测）
- 启用反向代理（可选）
- 配置后端服务地址

---

## 🔧 手动启动（备选）

如果启动脚本无法运行，手动执行：

```bash
# 1. 创建虚拟环境
python -m venv venv

# 2. 激活虚拟环境
# Windows
venv\Scripts\activate.bat
# Linux/macOS
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动 WAF
python main.py --port 8082
```

---

## 🎯 启动成功标志

看到以下信息说明启动成功：

```
[INFO] 🛡️ WAF system starting...
[OK] Rule engine loaded
  - Total rules: 14
  - Enabled rules: 14
[OK] Web interface ready
[INFO] Starting web server: 0.0.0.0:8082
[INFO] Press Ctrl+C to stop
```

---

## 🌐 访问管理界面

在浏览器中打开：`http://localhost:8082`

### 首页功能
- **仪表板** - 攻击统计和系统状态
- **日志** - 查询攻击日志
- **规则** - 管理 WAF 规则
- **白名单** - 配置 IP/URL 白名单
- **部署** - 配置运行模式和代理

---

## ❓ 常见问题

### Q: 启动时提示找不到 Python？
**A:** 需要安装 Python 3.8 或更高版本
- 下载: https://www.python.org/downloads/
- 安装时勾选 "Add Python to PATH"

### Q: 依赖安装很慢？
**A:** 使用国内镜像源
```bash
pip install -i https://pypi.tsinghua.edu.cn/simple -r requirements.txt
```

### Q: 如何修改管理界面端口？
**A:** 运行时指定 `--port` 参数
```bash
python main.py --port 9999
```
然后访问 `http://localhost:9999`

### Q: 如何启用反向代理？
**A:** 
1. 启动 WAF 后，进入管理界面
2. 切换到 **部署** 标签
3. 输入后端服务地址（如 http://localhost:8081）
4. 点击 **启动代理**
5. 代理会监听在 8080 端口

### Q: 如何停止 WAF？
**A:** 按 **Ctrl+C** 即可安全停止

---

## 📚 更多文档

- [docs/01_overview/00_START_HERE.md](docs/01_overview/00_START_HERE.md) - 完整导航
- [docs/05_operations/02_WEB_MANAGEMENT.md](docs/05_operations/02_WEB_MANAGEMENT.md) - Web 管理指南
- [docs/05_operations/03_ONE_CLICK_DEPLOYMENT.md](docs/05_operations/03_ONE_CLICK_DEPLOYMENT.md) - 一键部署指南

---

## 🎉 现在开始使用

1. 解压安装包
2. 运行 `start-waf.bat` (Windows) 或 `bash start-waf.sh` (Linux/macOS)
3. 打开 http://localhost:8082
4. 开始使用 WAF！

**祝你部署顺利！** 🚀
