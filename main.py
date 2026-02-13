"""
WAF系统 - 主入口
客户端请求 → 规则匹配引擎 → Web管理界面
"""
import sys
import os
import logging
import logging.handlers
import argparse
import json
from pathlib import Path
from datetime import datetime


def parse_size_bytes(size_str: str, default: int = 10 * 1024 * 1024) -> int:
    """解析 '100MB' 形式的字符串为字节数。"""
    try:
        s = size_str.strip().upper()
        if s.endswith('GB'):
            return int(float(s[:-2]) * 1024 * 1024 * 1024)
        if s.endswith('MB'):
            return int(float(s[:-2]) * 1024 * 1024)
        if s.endswith('KB'):
            return int(float(s[:-2]) * 1024)
        return int(float(s))
    except Exception:
        return default


def setup_directories():
    Path('logs').mkdir(parents=True, exist_ok=True)
    Path('models/saved').mkdir(parents=True, exist_ok=True)


def setup_logging(config):
    level = getattr(logging, config.logging.level, logging.INFO)
    max_bytes = parse_size_bytes(config.logging.max_size)
    backup_count = config.logging.backup_count

    log_file = Path(config.logging.error_log)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    handlers = [
        logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers,
        force=True
    )


logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src.core.rule_engine import RuleEngine
from src.web.app import WAFWebApp
from src.utils.web_tools import HTTPRequestParser
from src.utils.config_validator import load_and_validate_config


class WAFSystem:
    """WAF系统主类 - 客户端请求到规则匹配"""
    
    def __init__(self, config_path: str = "config/settings.yaml", mode: str = "protection"):
        """
        初始化WAF系统
        
        Args:
            config_path: 配置文件路径
            mode: 运行模式 (protection/detection)
        """
        self.config_path = config_path
        self.mode = mode

        # 载入并校验配置
        self.config = load_and_validate_config(self.config_path)
        setup_directories()
        setup_logging(self.config)
        
        logger.info("=" * 60)
        logger.info("[INIT] WAF system starting")
        logger.info("=" * 60)
        
        # 初始化规则引擎
        logger.info("[INIT] Loading rule engine...")
        self.rule_engine = RuleEngine(config_path)
        stats = self.rule_engine.get_stats()
        logger.info(f"[OK] Rule engine loaded")
        logger.info(f"  - Total rules: {stats['total_rules']}")
        logger.info(f"  - Enabled rules: {stats['enabled_rules']}")
        logger.info(f"  - Distribution: {stats['by_category']}")
        
        # 初始化Web管理界面
        logger.info("[INIT] Loading web interface...")
        self.web_app = WAFWebApp(config_path)
        logger.info("[OK] Web interface ready")
        
        logger.info(f"Mode: {self.mode} | URL: http://localhost:8082")
    
    def detect_request(self, request_data: dict) -> dict:
        """
        检测HTTP请求 - 使用规则匹配引擎
        
        Args:
            request_data: 包含URL、方法、头部、body等的请求数据
            
        Returns:
            {
                'blocked': bool,
                'reason': str,
                'rule_matches': list,
                'timestamp': str,
                'details': dict
            }
        """
        # 规则匹配检测
        is_attack, rule_matches = self.rule_engine.detect(request_data)
        
        # 决策：规则触发立即阻止
        should_block = is_attack
        
        result = {
            'blocked': should_block,
            'rule_triggered': is_attack,
            'rule_matches': rule_matches,
            'timestamp': datetime.now().isoformat()
        }
        
        if is_attack:
            result['reason'] = f"规则匹配: {rule_matches[0].get('rule_name', '未知')}"
            result['severity'] = rule_matches[0].get('severity', 'medium')
            result['category'] = rule_matches[0].get('category', 'unknown')
        else:
            result['reason'] = '正常请求'
            result['severity'] = 'low'
            result['category'] = 'normal'
        
        return result
    
    def run_web_server(self, host: str = '0.0.0.0', port: int = 8080, debug: bool = False):
        """启动Web管理服务器"""
        self.web_app.run(host=host, port=port, debug=debug)
    
    def get_status(self) -> dict:
        """获取系统状态"""
        return {
            'mode': self.mode,
            'rule_engine': self.rule_engine.get_stats(),
            'web_interface': 'running'
        }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='WAF系统 - 规则匹配引擎')
    parser.add_argument('--mode', default='protection', 
                       choices=['protection', 'detection'],
                       help='运行模式')
    parser.add_argument('--host', default='0.0.0.0',
                       help='Web服务器主机')
    parser.add_argument('--port', type=int, default=8082,
                       help='Web服务器端口')
    parser.add_argument('--config', default='config/settings.yaml',
                       help='配置文件路径')
    parser.add_argument('--debug', action='store_true',
                       help='Debug模式')
    
    args = parser.parse_args()
    
    try:
        # 创建WAF系统实例
        waf_system = WAFSystem(config_path=args.config, mode=args.mode)
        
        # 显示系统状态
        logger.info("\n[INFO] System Status:")
        status = waf_system.get_status()
        logger.info(f"  Mode: {status['mode']}")
        logger.info(f"  Rules: {status['rule_engine']}\n")
        
        # 启动Web服务器
        logger.info(f"[INFO] Starting web server: http://{args.host}:{args.port}")
        logger.info("[INFO] Press Ctrl+C to stop\n")
        
        waf_system.run_web_server(host=args.host, port=args.port, debug=args.debug)
    
    except KeyboardInterrupt:
        logger.info("\n[SHUTDOWN] System stopped gracefully")
    except Exception as e:
        logger.error(f"[ERROR] System error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
