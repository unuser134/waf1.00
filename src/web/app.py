"""
Web管理界面 - Flask应用
客户端请求监控和规则管理
"""
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from datetime import datetime, timedelta
from pathlib import Path
import yaml
import json
import logging
from typing import Dict, Any, List
from collections import defaultdict, deque
import threading
import subprocess
import shlex
import sys

logger = logging.getLogger(__name__)


class AttackLog:
    """攻击日志管理 - 内存缓存"""
    
    def __init__(self, max_size: int = 10000):
        """初始化日志管理器"""
        self.logs: deque = deque(maxlen=max_size)
        self.lock = threading.Lock()
    
    def add_log(self, log_entry: Dict[str, Any]):
        """添加日志"""
        log_entry['timestamp'] = datetime.now().isoformat()
        with self.lock:
            self.logs.append(log_entry)
    
    def get_logs(self, limit: int = 100, filter_type: str = None) -> List[Dict[str, Any]]:
        """获取日志"""
        with self.lock:
            logs = list(self.logs)
        
        # 倒序排列（最新的在前）
        logs.reverse()
        
        # 支持 category 和 type 字段过滤
        if filter_type:
            logs = [log for log in logs if log.get('category') == filter_type or log.get('type') == filter_type]
        
        return logs[:limit]
    
    def get_stats(self, hours: int = 24) -> Dict[str, Any]:
        """获取统计信息"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self.lock:
            recent_logs = []
            for log in self.logs:
                try:
                    log_time = datetime.fromisoformat(log.get('timestamp', ''))
                    if log_time > cutoff_time:
                        recent_logs.append(log)
                except (ValueError, TypeError):
                    # 处理时间戳解析错误
                    recent_logs.append(log)
        
        # 按攻击类型、规则、URL、源IP统计
        attack_count = defaultdict(int)
        severity_count = defaultdict(int)
        hourly_count = defaultdict(int)
        rule_count = defaultdict(int)
        url_count = defaultdict(int)
        source_count = defaultdict(int)
        
        for log in recent_logs:
            attack_count[log.get('category', 'unknown')] += 1
            severity_count[log.get('severity', 'unknown')] += 1
            rule_count[log.get('rule', 'unknown')] += 1
            url_count[log.get('request_url', 'unknown')] += 1
            source_count[log.get('source_ip', 'unknown')] += 1
            
            try:
                log_time = datetime.fromisoformat(log.get('timestamp', ''))
                hour_key = log_time.strftime('%Y-%m-%d %H:00')
                hourly_count[hour_key] += 1
            except (ValueError, TypeError):
                pass
        
        # 获取排名前5的最常攻击URL和攻击源
        top_urls = sorted(url_count.items(), key=lambda x: x[1], reverse=True)[:5]
        top_attackers = sorted(source_count.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total': len(recent_logs),
            'total_attacks': len(recent_logs),
            'by_category': dict(attack_count),
            'by_severity': dict(severity_count),
            'hourly_trend': dict(sorted(hourly_count.items())),
            'by_rule': dict(rule_count),
            'top_attacked_urls': [{'url': url, 'count': count} for url, count in top_urls],
            'top_attackers': [{'source_ip': ip, 'count': count} for ip, count in top_attackers]
        }


class WAFWebApp:
    """WAF Web应用"""
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        """初始化Web应用"""
        # 使用绝对路径确保模板和静态文件能被找到
        base_dir = Path(__file__).parent
        self.app = Flask(__name__, 
                        template_folder=str(base_dir / 'templates'),
                        static_folder=str(base_dir / 'static'))
        CORS(self.app)
        
        self.config_path = Path(config_path)
        self.attack_log = AttackLog()
        self.whitelist = set()
        self.blacklist = set()
        self.rule_engine = None
        self.mode = 'protection'
        self.proxy_process = None
        
        self.load_config()
        self.setup_routes()
        # 在每次请求前记录基本信息，便于调试不支持的媒体类型错误
        @self.app.before_request
        def _log_before_request():
            try:
                logger.info(f"Incoming request: {request.method} {request.path} headers={dict(request.headers)}")
            except Exception:
                pass
    
    def load_config(self):
        """加载配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            
            # 加载白名单
            whitelist_file = config.get('whitelist', {}).get('file')
            if whitelist_file and Path(whitelist_file).exists():
                with open(whitelist_file, 'r', encoding='utf-8') as f:
                    whitelist_data = yaml.safe_load(f) or {}
                    self.whitelist = set(whitelist_data.get('whitelist_ips', []))
                    self.whitelist.update(whitelist_data.get('whitelist_paths', []))
            
            logger.info(f"加载白名单: {len(self.whitelist)} 条")
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
    
    def setup_routes(self):
        """设置路由"""
        # 初始化规则引擎实例，供 UI 使用
        try:
            from src.core.rule_engine import RuleEngine
            self.rule_engine = RuleEngine(self.config_path)
        except Exception:
            self.rule_engine = None
        
        @self.app.route('/')
        def index():
            """主页 - 仪表板"""
            return render_template('dashboard.html')

        @self.app.route('/favicon.ico')
        def favicon():
            """提供 favicon，避免 404"""
            try:
                return send_file(Path(__file__).parent / 'static' / 'favicon.ico', mimetype='image/x-icon')
            except Exception:
                return ('', 204)
        
        @self.app.route('/api/stats', methods=['GET'])
        def get_stats():
            """获取统计信息"""
            hours = request.args.get('hours', 24, type=int)
            stats = self.attack_log.get_stats(hours=hours)
            return jsonify(stats)
        
        @self.app.route('/api/logs', methods=['GET'])
        def get_logs():
            """获取攻击日志"""
            limit = request.args.get('limit', 100, type=int)
            # 避免无界查询，限制在 1-500 条
            limit = max(1, min(limit, 500))
            log_type = request.args.get('type', None)
            
            logs = self.attack_log.get_logs(limit=limit, filter_type=log_type)
            return jsonify({'logs': logs, 'count': len(logs)})
        
        @self.app.route('/api/logs', methods=['POST'])
        def add_log():
            """添加日志"""
            log_entry = request.get_json()
            self.attack_log.add_log(log_entry)
            return jsonify({'status': 'success'})
        
        @self.app.route('/api/rules', methods=['GET'])
        def get_rules():
            """获取规则统计"""
            if self.rule_engine:
                return jsonify(self.rule_engine.get_stats())
            return jsonify({'message': 'rule engine not available'})
        
        @self.app.route('/api/rules/reload', methods=['POST'])
        def reload_rules():
            """重新加载规则"""
            if self.rule_engine:
                try:
                    self.rule_engine.reload_rules()
                    return jsonify({'status': 'success', 'message': 'Rules reloaded'})
                except Exception as e:
                    return jsonify({'status': 'error', 'message': str(e)}), 500
            return jsonify({'status': 'error', 'message': 'rule engine not available'}), 500
        
        @self.app.route('/api/whitelist', methods=['GET'])
        def get_whitelist():
            """获取白名单"""
            return jsonify({
                'whitelist': list(self.whitelist),
                'count': len(self.whitelist)
            })
        
        @self.app.route('/api/whitelist', methods=['POST'])
        def add_whitelist():
            """添加白名单项"""
            # 支持 JSON 和表单提交两种方式
            data = {}
            if request.is_json:
                try:
                    data = request.get_json() or {}
                except Exception:
                    data = {}
            else:
                # Flask 会把表单数据放在 request.form
                try:
                    data = request.form.to_dict() or {}
                except Exception:
                    data = {}

            # 支持多种字段名：item、ip
            item = data.get('item') or data.get('ip') or None

            if item:
                self.whitelist.add(item)
                return jsonify({'status': 'success', 'item': item})

            # 尝试解析原始请求体（例如 tests 中使用的原始字符串 data="ip=..."）
            raw = request.get_data(as_text=True) or ''
            if raw and '=' in raw:
                try:
                    k, v = raw.split('=', 1)
                    if k.strip() in ('ip', 'item') and v:
                        self.whitelist.add(v.strip())
                        return jsonify({'status': 'success', 'item': v.strip()})
                except Exception:
                    pass

            return jsonify({'status': 'error', 'message': 'Invalid item'}), 400
        
        @self.app.route('/api/whitelist/<item>', methods=['DELETE'])
        def remove_whitelist(item):
            """移除白名单项"""
            self.whitelist.discard(item)
            return jsonify({'status': 'success'})

        @self.app.route('/api/deploy/mode', methods=['POST'])
        def set_mode():
            data = request.get_json() or {}
            mode = data.get('mode')
            if mode in ('protection', 'detection'):
                self.mode = mode
                return jsonify({'status': 'success', 'mode': self.mode})
            return jsonify({'status': 'error', 'message': 'invalid mode'}), 400

        @self.app.route('/api/deploy/proxy/start', methods=['POST'])
        def start_proxy():
            data = request.get_json() or {}
            backend = data.get('backend')
            port = data.get('port', 8080)
            if not backend:
                return jsonify({'status': 'error', 'message': 'backend required'}), 400
            if self.proxy_process and self.proxy_process.poll() is None:
                return jsonify({'status': 'error', 'message': 'proxy already running'}), 400
            try:
                # pass current UI host url so proxy can post logs back to AttackLog
                waf_ui = request.host_url.rstrip('/')
                cmd = [
                    sys.executable,
                    str(Path(__file__).parent.parent.parent / 'scripts' / 'waf_reverse_proxy.py'),
                    '--backend', backend,
                    '--port', str(port),
                    '--waf-ui', waf_ui
                ]
                # start subprocess detached
                self.proxy_process = subprocess.Popen(cmd)
                return jsonify({'status': 'success', 'pid': self.proxy_process.pid})
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500

        @self.app.route('/api/deploy/proxy/stop', methods=['POST'])
        def stop_proxy():
            if not self.proxy_process:
                return jsonify({'status': 'error', 'message': 'no proxy running'}), 400
            try:
                self.proxy_process.terminate()
                self.proxy_process.wait(timeout=5)
                self.proxy_process = None
                return jsonify({'status': 'success'})
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500

        @self.app.route('/api/deploy/status', methods=['GET'])
        def deploy_status():
            proxy_status = 'stopped'
            pid = None
            if self.proxy_process and self.proxy_process.poll() is None:
                proxy_status = 'running'
                pid = self.proxy_process.pid
            return jsonify({'mode': self.mode, 'proxy': {'status': proxy_status, 'pid': pid}})
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """健康检查"""
            rule_stats = {}
            if self.rule_engine:
                try:
                    rule_stats = self.rule_engine.get_stats()
                except Exception:
                    rule_stats = {}
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'logs_count': len(self.attack_log.logs),
                'rules_total': rule_stats.get('total_rules'),
                'rules_enabled': rule_stats.get('enabled_rules'),
                'rules_version': rule_stats.get('latest_rule_version'),
                'rules_release_date': rule_stats.get('latest_rule_release_date'),
                'rule_engine_load_ms': rule_stats.get('load_duration_ms')
            })
        
        @self.app.route('/api/export/logs', methods=['GET'])
        def export_logs():
            """导出日志"""
            logs = self.attack_log.get_logs(limit=10000)
            
            # 导出为JSON
            json_path = Path('logs/export') / f'logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            json_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
            
            return send_file(json_path, as_attachment=True)
    
    def run(self, host: str = '0.0.0.0', port: int = 8080, debug: bool = False):
        """运行Web应用"""
        logger.info(f"启动WAF Web管理界面: {host}:{port}")
        self.app.run(host=host, port=port, debug=debug, threaded=True)
