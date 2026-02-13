"""
DL混合WAF系统包 - 传统WAF核心（1.0版本）
深度学习部分将在2.0版本中添加
"""
from .core.rule_engine import RuleEngine, Rule
from .web.app import WAFWebApp, AttackLog
from .utils.web_tools import HTTPRequestParser, URLDecoder, ContentAnalyzer, ResponseBuilder

# 深度学习模块延迟导入 (可选，用于2.0版本)
def load_dl_module():
    """按需导入深度学习模块，避免强制依赖PyTorch"""
    try:
        from .core.dl_detector import DLDetector, DLDetectionModel, FeatureExtractor
        return DLDetector, DLDetectionModel, FeatureExtractor
    except ImportError:
        raise ImportError("深度学习模块需要 PyTorch，请运行: pip install torch")

__version__ = '1.0.0'
__author__ = 'DL-WAF Team'

__all__ = [
    'RuleEngine',
    'Rule',
    'WAFWebApp',
    'AttackLog',
    'HTTPRequestParser',
    'URLDecoder',
    'ContentAnalyzer',
    'ResponseBuilder',
    'load_dl_module',  # 2.0版本用
]
