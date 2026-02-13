#!/usr/bin/env python3
"""
DL混合WAF 1.0 - 部署向导（可视化安装程序）
提供交互式 CLI 界面指导用户安装和配置 WAF
"""
import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Optional

class Colors:
    """ANSI 颜色代码"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_header(title: str):
    """打印标题"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}  {title}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")

def print_success(msg: str):
    """打印成功信息"""
    print(f"{Colors.GREEN}✅  {msg}{Colors.END}")

def print_error(msg: str):
    """打印错误信息"""
    print(f"{Colors.RED}❌  {msg}{Colors.END}")

def print_warning(msg: str):
    """打印警告信息"""
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")

def print_info(msg: str):
    """打印信息"""
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")

def run_command(cmd: list, show_output: bool = True) -> tuple[bool, str]:
    """执行命令，返回 (成功与否, 输出)"""
    try:
        if show_output:
            result = subprocess.run(cmd, check=True, text=True)
            return True, ""
        else:
            result = subprocess.run(cmd, capture_output=True, check=True, text=True)
            return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr or str(e)
    except Exception as e:
        return False, str(e)

def check_python_version() -> bool:
    """检查 Python 版本"""
    print_info(f"Python 版本: {sys.version.split()[0]}")
    if sys.version_info >= (3, 8):
        print_success("Python 版本符合要求 (≥3.8)")
        return True
    else:
        print_error("需要 Python 3.8 或更高版本")
        return False

def check_venv() -> bool:
    """检查是否在虚拟环境中"""
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    if in_venv:
        print_success("已在虚拟环境中")
        return True
    else:
        print_warning("未检测到虚拟环境，建议创建虚拟环境以避免依赖冲突")
        return False

def install_dependencies() -> bool:
    """安装依赖"""
    print_header("📦 安装依赖")
    
    # 检查 requirements-1.0.txt
    req_file = Path(__file__).parent / "requirements-1.0.txt"
    if not req_file.exists():
        print_error(f"找不到 {req_file}")
        return False
    
    print_info(f"从 {req_file} 安装依赖...")
    success, output = run_command(
        [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
        show_output=True
    )
    
    if success:
        print_success("依赖安装完成")
        return True
    else:
        print_error(f"依赖安装失败:\n{output}")
        return False

def configure_waf() -> dict:
    """交互式配置 WAF"""
    print_header("⚙️  配置 WAF")
    
    config = {}
    
    # WAF UI 端口
    print_info("WAF 管理界面端口 (默认: 8082)")
    port = input(f"{Colors.BLUE}➜ {Colors.END}").strip() or "8082"
    try:
        config['ui_port'] = int(port)
    except ValueError:
        print_error("端口必须是整数")
        return {}
    
    # 运行模式
    print_info("\n运行模式:")
    print("  1. protection (保护模式 - 阻止攻击)")
    print("  2. detection  (检测模式 - 仅记录)")
    mode = input(f"{Colors.BLUE}➜ {Colors.END}").strip() or "1"
    config['mode'] = 'detection' if mode == "2" else 'protection'
    
    # 代理配置（可选）
    print_info("\n是否启用反向代理? (y/n, 默认: n)")
    enable_proxy = input(f"{Colors.BLUE}➜ {Colors.END}").strip().lower() == 'y'
    
    if enable_proxy:
        print_info("后端服务地址 (例如: http://localhost:8081)")
        backend = input(f"{Colors.BLUE}➜ {Colors.END}").strip() or "http://localhost:8081"
        config['proxy_backend'] = backend
        
        print_info("代理端口 (默认: 8080)")
        proxy_port = input(f"{Colors.BLUE}➜ {Colors.END}").strip() or "8080"
        try:
            config['proxy_port'] = int(proxy_port)
        except ValueError:
            print_error("端口必须是整数")
            return {}
    
    return config

def create_startup_script(config: dict) -> bool:
    """创建启动脚本"""
    print_header("📝 创建启动脚本")
    
    project_root = Path(__file__).parent
    
    # 创建 Windows 批处理文件
    batch_content = f"""@echo off
REM DL混合WAF 1.0 - Windows 启动脚本
echo.
echo {Colors.CYAN}🛡️ DL混合WAF 1.0 - 启动中...{Colors.END}
echo.

cd /d {project_root}

REM 检查虚拟环境
if not exist "venv" (
    echo {Colors.YELLOW}⚠️ 未找到虚拟环境，正在创建...{Colors.END}
    python -m venv venv
)

REM 激活虚拟环境
call venv\\Scripts\\activate.bat

REM 启动 WAF UI
echo {Colors.GREEN}✅ 启动 WAF 管理界面 (端口 {config.get('ui_port', 8082)})...{Colors.END}
python main.py --port {config.get('ui_port', 8082)}

pause
"""
    
    batch_file = project_root / "start-waf.bat"
    with open(batch_file, 'w', encoding='utf-8') as f:
        f.write(batch_content)
    print_success(f"创建启动脚本: {batch_file}")
    
    # 创建 Linux/macOS Shell 脚本
    shell_content = f"""#!/bin/bash
# DL混合WAF 1.0 - Linux/macOS 启动脚本
echo
echo "🛡️  DL混合WAF 1.0 - 启动中..."
echo

cd "{project_root}"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "⚠️  未找到虚拟环境，正在创建..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 启动 WAF UI
echo "✅ 启动 WAF 管理界面 (端口 {config.get('ui_port', 8082)})..."
python main.py --port {config.get('ui_port', 8082)}
"""
    
    shell_file = project_root / "start-waf.sh"
    with open(shell_file, 'w', encoding='utf-8') as f:
        f.write(shell_content)
    os.chmod(shell_file, 0o755)
    print_success(f"创建启动脚本: {shell_file}")
    
    # 保存配置
    config_file = project_root / "waf-config.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print_success(f"保存配置: {config_file}")
    
    return True

def display_next_steps(config: dict):
    """显示后续步骤"""
    print_header("🚀 部署完成！")
    
    project_root = Path(__file__).parent
    ui_port = config.get('ui_port', 8082)
    
    print_success("WAF 1.0 已安装完成！")
    print()
    
    print(f"{Colors.BOLD}接下来的步骤:{Colors.END}")
    print()
    
    # Windows
    if sys.platform == 'win32':
        print(f"1. {Colors.BOLD}启动 WAF:{Colors.END}")
        print(f"   {Colors.CYAN}双击 start-waf.bat{Colors.END} 或运行:")
        print(f"   {Colors.CYAN}python main.py --port {ui_port}{Colors.END}")
    else:
        print(f"1. {Colors.BOLD}启动 WAF:{Colors.END}")
        print(f"   {Colors.CYAN}bash start-waf.sh{Colors.END} 或运行:")
        print(f"   {Colors.CYAN}python main.py --port {ui_port}{Colors.END}")
    
    print()
    print(f"2. {Colors.BOLD}打开管理界面:{Colors.END}")
    print(f"   {Colors.CYAN}http://localhost:{ui_port}{Colors.END}")
    
    if config.get('proxy_backend'):
        print()
        print(f"3. {Colors.BOLD}启动反向代理:{Colors.END}")
        print(f"   {Colors.CYAN}python scripts/waf_reverse_proxy.py --backend {config.get('proxy_backend')} --port {config.get('proxy_port', 8080)} --waf-ui http://localhost:{ui_port}{Colors.END}")
        print(f"   {Colors.CYAN}代理地址: http://localhost:{config.get('proxy_port', 8080)}{Colors.END}")
    
    print()
    print(f"{Colors.BOLD}默认用户:{Colors.END}")
    print(f"  无需认证，直接访问管理界面")
    print()
    print(f"{Colors.BOLD}文档:{Colors.END}")
    print(f"  {Colors.CYAN}README.md{Colors.END} - 项目说明")
    print(f"  {Colors.CYAN}START_HERE.md{Colors.END} - 快速开始")
    print()

def main():
    """主函数"""
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print_header("🛡️ DL混合WAF 1.0 - 部署向导")
    
    # 步骤 1: 检查环境
    print_header("🔍 环境检查")
    if not check_python_version():
        sys.exit(1)
    check_venv()
    
    # 步骤 2: 安装依赖
    if not install_dependencies():
        sys.exit(1)
    
    # 步骤 3: 配置 WAF
    config = configure_waf()
    if not config:
        print_error("配置失败")
        sys.exit(1)
    
    print_success(f"配置完成: {json.dumps(config, ensure_ascii=False)}")
    
    # 步骤 4: 创建启动脚本
    if not create_startup_script(config):
        sys.exit(1)
    
    # 步骤 5: 显示后续步骤
    display_next_steps(config)
    
    print(f"{Colors.GREEN}{Colors.BOLD}✨ 部署向导完成！{Colors.END}")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_error("安装被中断")
        sys.exit(1)
    except Exception as e:
        print_error(f"发生错误: {e}")
        sys.exit(1)
