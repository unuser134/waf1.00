"""
WAF系统演示和测试脚本
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.rule_engine import RuleEngine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_rule_engine():
    """测试规则引擎"""
    print("\n" + "="*60)
    print("测试1: 规则引擎 (RuleEngine)")
    print("="*60)
    
    engine = RuleEngine()
    
    # 测试样本请求
    test_cases = [
        {
            'name': 'SQL注入攻击',
            'data': {
                'url': '/api/user?id=1 OR 1=1',
                'method': 'GET',
                'body': ''
            }
        },
        {
            'name': 'XSS攻击',
            'data': {
                'url': '/search',
                'method': 'POST',
                'body': '<script>alert("XSS")</script>'
            }
        },
        {
            'name': '目录遍历',
            'data': {
                'url': '/files?path=../../etc/passwd',
                'method': 'GET',
                'body': ''
            }
        },
        {
            'name': '正常请求',
            'data': {
                'url': '/api/users',
                'method': 'GET',
                'body': ''
            }
        }
    ]
    
    for test in test_cases:
        is_attack, matches = engine.detect(test['data'])
        print(f"\n✓ 测试: {test['name']}")
        print(f"  结果: {'🚨 检测到攻击' if is_attack else '✓ 正常'}")
        if matches:
            print(f"  匹配规则:")
            for match in matches[:3]:  # 显示前3个
                print(f"    - {match['rule_name']} ({match['category']}, 严重度: {match['severity']})")
    
    # 统计信息
    stats = engine.get_stats()
    print(f"\n规则统计:")
    print(f"  总规则数: {stats['total_rules']}")
    print(f"  启用规则: {stats['enabled_rules']}")
    print(f"  按类别:")
    for category, count in stats['by_category'].items():
        print(f"    - {category}: {count}")


def test_hybrid_detection():
    """测试规则匹配检测"""
    print("\n" + "="*60)
    print("测试2: 规则匹配检测")
    print("="*60)
    
    rule_engine = RuleEngine()
    
    # 模拟一个可疑请求
    request_data = {
        'url': '/api/admin?id=1 OR 1=1',
        'method': 'POST',
        'headers': {'User-Agent': 'Mozilla/5.0'},
        'body': 'username=admin&password=" OR "1"="1',
        'query_string': 'id=1 OR 1=1'
    }
    
    print("\n测试请求:")
    print(f"  URL: {request_data['url']}")
    print(f"  Body: {request_data['body']}")
    
    # 规则检测
    rule_triggered, rule_matches = rule_engine.detect(request_data)
    
    print(f"\n检测结果:")
    print(f"  规则匹配: {'是' if rule_triggered else '否'}")
    if rule_matches:
        print(f"    触发规则: {rule_matches[0]['rule_name']}")
    
    # 决策
    should_block = rule_triggered
    print(f"\n✓ 最终决策: {'🚨 阻止请求' if should_block else '✓ 放行请求'}")


if __name__ == '__main__':
    test_rule_engine()
    test_hybrid_detection()
    
    print("\n" + "="*60)
    print("✓ 所有测试完成！")
    print("="*60)
