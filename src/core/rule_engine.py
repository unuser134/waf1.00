"""
规则匹配引擎 - 传统WAF核心
基于YAML规则文件进行HTTP请求检测
"""
import yaml
import re
import time
from typing import List, Dict, Any, Tuple
from pathlib import Path
from dataclasses import dataclass
import logging

from src.utils.web_tools import HTTPRequestParser

logger = logging.getLogger(__name__)


@dataclass
class Rule:
    """单条WAF规则"""
    name: str
    category: str  # sql_injection, xss, directory_traversal, etc.
    patterns: List[str]  # 正则表达式列表
    severity: str  # critical, high, medium, low
    enabled: bool = True
    priority: int = 999  # 优先级（1最高，999最低），用于排序检测顺序
    confidence: float = 1.0  # 置信度（0.0-1.0），未来可用于DL融合
    cost_level: str = "accurate"  # fast, accurate, expensive

    def __post_init__(self):
        self.compiled_patterns = []
        for pattern in self.patterns:
            try:
                self.compiled_patterns.append(re.compile(pattern, re.IGNORECASE))
            except re.error as e:
                logger.error(f"规则 {self.name} 正则表达式错误: {e}")
    
    def match(self, text: str) -> bool:
        """检查文本是否匹配规则"""
        if not self.enabled:
            return False
        for pattern in self.compiled_patterns:
            if pattern.search(text):
                return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """将 Rule 对象转换为字典表示，便于序列化和兼容旧代码"""
        return {
            'name': self.name,
            'category': self.category,
            'patterns': list(self.patterns),
            'severity': self.severity,
            'enabled': self.enabled,
            'cost_level': self.cost_level
        }

    def __contains__(self, key: str) -> bool:
        """允许使用 `'name' in rule` 这种旧式检测方式。
        返回 True 当且仅当该属性存在。
        """
        return hasattr(self, key)


class RuleEngine:
    """WAF规则引擎"""
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        """初始化规则引擎"""
        self.config_path = Path(config_path)
        self.rules: List[Rule] = []
        self.rule_files: List[str] = []
        self.rule_metadata: List[Dict[str, Any]] = []
        self.severity_levels = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        self.cost_rank = {"fast": 0, "accurate": 1, "expensive": 2}
        self.cache_ttl_seconds = 5
        self.match_cache: Dict[str, Tuple[float, Tuple[bool, List[Dict[str, Any]]]]] = {}
        self.load_duration_ms = 0
        self.load_config()
        self.load_rules()
    
    def load_config(self):
        """从配置文件加载规则文件列表"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                self.rule_files = config.get('rules', {}).get('directories', [])
                self.cache_ttl_seconds = int(config.get('detection', {}).get('cache_ttl_seconds', 5))
                logger.info(f"加载规则文件配置: {self.rule_files}")
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            self.rule_files = []
    
    def load_rules(self):
        """从YAML文件加载所有规则"""
        start_time = time.monotonic()
        for rule_file in self.rule_files:
            try:
                with open(rule_file, 'r', encoding='utf-8') as f:
                    rule_data = yaml.safe_load(f) or {}
                    metadata = rule_data.get('metadata') or {}
                    if metadata:
                        self.rule_metadata.append(metadata)
                    if 'rules' in rule_data:
                        for rule_dict in rule_data['rules']:
                            rule = Rule(
                                name=rule_dict.get('name', ''),
                                category=rule_dict.get('category', ''),
                                patterns=rule_dict.get('patterns', []),
                                severity=rule_dict.get('severity', 'medium'),
                                enabled=rule_dict.get('enabled', True),
                                priority=rule_dict.get('priority', 999),  # 新增：支持优先级
                                confidence=rule_dict.get('confidence', 1.0),  # 新增：支持置信度
                                cost_level=rule_dict.get('cost_level', 'accurate')
                            )
                            self.rules.append(rule)
                logger.info(f"从 {rule_file} 加载 {len(rule_data.get('rules', []))} 条规则")
            except FileNotFoundError:
                logger.warning(f"规则文件不存在: {rule_file}")
            except Exception as e:
                logger.error(f"加载规则文件 {rule_file} 失败: {e}")
        self.load_duration_ms = int((time.monotonic() - start_time) * 1000)
    
    def detect(self, request_data: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        检测请求是否包含攻击
        
        Args:
            request_data: 包含URL、方法、头部、body等的请求数据
            
        Returns:
            (是否检测到攻击, 匹配的规则列表)
        """
        matched_rules = []

        # 命中缓存：同一 URI + IP 短时间内直接复用结果
        src_ip = request_data.get('source_ip', '') or ''
        uri = request_data.get('url', '') or ''
        cache_key = f"{src_ip}|{uri}"
        now = time.monotonic()
        cached = self.match_cache.get(cache_key)
        if cached and (now - cached[0]) <= self.cache_ttl_seconds:
            return cached[1]
        if cached:
            self.match_cache.pop(cache_key, None)
        
        normalized = HTTPRequestParser.normalize_request(request_data)
        check_strings = [
            normalized.get('url', ''),
            normalized.get('method', ''),
            str(normalized.get('headers', {})),
            normalized.get('body', ''),
            normalized.get('query_string', ''),
        ]

        # 分层匹配：fast -> accurate -> expensive
        sorted_rules = sorted(
            self.rules,
            key=lambda r: (self.cost_rank.get(r.cost_level, 1), r.priority)
        )
        
        for rule in sorted_rules:
            for check_str in check_strings:
                if rule.match(check_str):
                    matched_rules.append({
                        'rule_id': rule.name,
                        'rule_name': rule.name,
                        'category': rule.category,
                        'severity': rule.severity,
                        'priority': rule.priority,
                        'confidence': rule.confidence,
                        'cost_level': rule.cost_level,
                        'matched_text': check_str[:100]  # 仅保留前100字符
                    })
        
        # 去重：按规则名称去重，保留最高严重级别
        unique_rules = {}
        for rule in matched_rules:
            key = rule['rule_name']
            if key not in unique_rules or \
               self.severity_levels.get(rule['severity'], 0) > \
               self.severity_levels.get(unique_rules[key]['severity'], 0):
                unique_rules[key] = rule
        
        matched_rules = list(unique_rules.values())
        result = (len(matched_rules) > 0, matched_rules)
        self.match_cache[cache_key] = (now, result)
        return result
    
    def reload_rules(self):
        """重新加载规则"""
        self.rules.clear()
        self.load_config()
        self.load_rules()
        logger.info("规则已重新加载")

    def get_all_rules(self) -> List[Dict[str, Any]]:
        """返回规则的列表（字典格式），向后兼容期望字典的调用者。

        如果内部使用的是对象列表，会将每个 Rule 转换为字典。
        """
        return [r.to_dict() if hasattr(r, 'to_dict') else r for r in self.rules]
    
    def get_rules_by_category(self, category: str) -> List[Rule]:
        """按类别获取规则"""
        return [r for r in self.rules if r.category == category]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取规则统计信息"""
        categories = {}
        severity_dist = {}
        
        for rule in self.rules:
            categories[rule.category] = categories.get(rule.category, 0) + 1
            severity_dist[rule.severity] = severity_dist.get(rule.severity, 0) + 1
        
        latest_version = None
        latest_release = None
        for meta in self.rule_metadata:
            version = meta.get('version')
            release_date = meta.get('release_date')
            if version and (latest_version is None or version > latest_version):
                latest_version = version
            if release_date and (latest_release is None or release_date > latest_release):
                latest_release = release_date

        return {
            'total_rules': len(self.rules),
            'enabled_rules': sum(1 for r in self.rules if r.enabled),
            'by_category': categories,
            'by_severity': severity_dist,
            'latest_rule_version': latest_version,
            'latest_rule_release_date': latest_release,
            'load_duration_ms': self.load_duration_ms
        }
