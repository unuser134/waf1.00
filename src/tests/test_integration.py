#!/usr/bin/env python
"""
集成测试脚本 - 测试WAF系统所有主要功能
包括规则引擎、Web API、日志管理等
"""
import sys
import time
import requests
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.core.rule_engine import RuleEngine
from src.web.app import WAFWebApp, AttackLog

# 测试配置
BASE_URL = "http://localhost:8080"
TEST_RESULTS = {
    'passed': 0,
    'failed': 0,
    'errors': []
}

def test_result(test_name, passed, message=""):
    """记录测试结果"""
    if passed:
        TEST_RESULTS['passed'] += 1
        print(f"  ✓ {test_name}")
    else:
        TEST_RESULTS['failed'] += 1
        error_msg = f"✗ {test_name}"
        if message:
            error_msg += f": {message}"
        print(error_msg)
        TEST_RESULTS['errors'].append(error_msg)

def test_rule_engine():
    """测试1: 规则引擎功能"""
    print("\n" + "="*70)
    print("TEST 1: Rule Engine")
    print("="*70)
    
    engine = RuleEngine()
    
    # 测试规则加载
    stats = engine.get_stats()
    test_result(
        "Load 14 rules",
        stats['total_rules'] == 14,
        f"Got {stats['total_rules']} rules"
    )
    
    # 测试SQL注入检测
    sql_payload = {'url': '/api/user?id=1 OR 1=1', 'method': 'GET', 'body': ''}
    is_attack, matches = engine.detect(sql_payload)
    test_result(
        "Detect SQL Injection",
        is_attack and len(matches) > 0,
        f"Matched {len(matches)} rule(s)" if is_attack else "No rules matched"
    )
    
    # 测试XSS检测
    xss_payload = {'url': '/search', 'method': 'POST', 'body': '<script>alert(1)</script>'}
    is_attack, matches = engine.detect(xss_payload)
    test_result(
        "Detect XSS Attack",
        is_attack and len(matches) > 0,
        f"Matched {len(matches)} rule(s)" if is_attack else "No rules matched"
    )
    
    # 测试正常请求
    normal_payload = {'url': '/api/users', 'method': 'GET', 'body': ''}
    is_attack, matches = engine.detect(normal_payload)
    test_result(
        "Allow Normal Request",
        not is_attack,
        "Incorrectly blocked" if is_attack else "Allowed"
    )
    
    # 测试规则统计
    test_result(
        "Rule statistics",
        'by_category' in stats and 'by_severity' in stats,
        f"Categories: {len(stats['by_category'])}, Severities: {len(stats['by_severity'])}"
    )


def test_attack_log():
    """测试2: 日志管理"""
    print("\n" + "="*70)
    print("TEST 2: Attack Log Management")
    print("="*70)
    
    log = AttackLog()
    
    # 添加日志
    log.add_log({'category': 'sql_injection', 'severity': 'critical', 'source_ip': '192.168.1.1'})
    log.add_log({'category': 'xss', 'severity': 'high', 'source_ip': '192.168.1.2'})
    
    # 获取日志
    logs = log.get_logs(limit=100)
    test_result(
        "Add and retrieve logs",
        len(logs) == 2,
        f"Retrieved {len(logs)} logs"
    )
    
    # 按类别过滤
    sql_logs = log.get_logs(limit=100, filter_type='sql_injection')
    test_result(
        "Filter logs by category",
        len(sql_logs) == 1,
        f"Found {len(sql_logs)} SQL injection log(s)"
    )
    
    # 获取统计信息
    stats = log.get_stats(hours=24)
    test_result(
        "Get log statistics",
        'total' in stats and 'by_category' in stats,
        f"Total attacks: {stats.get('total', 0)}"
    )


def test_web_api():
    """测试3: Web API端点"""
    print("\n" + "="*70)
    print("TEST 3: Web API Endpoints")
    print("="*70)
    
    time.sleep(1)  # 等待服务器完全启动
    
    try:
        # 测试健康检查
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        test_result(
            "GET /api/health",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        
        # 测试获取统计信息
        response = requests.get(f"{BASE_URL}/api/stats?hours=24", timeout=5)
        test_result(
            "GET /api/stats",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        
        # 测试获取日志
        response = requests.get(f"{BASE_URL}/api/logs?limit=10", timeout=5)
        test_result(
            "GET /api/logs",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        
        # 测试获取规则
        response = requests.get(f"{BASE_URL}/api/rules", timeout=5)
        test_result(
            "GET /api/rules",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        
        # 测试获取白名单
        response = requests.get(f"{BASE_URL}/api/whitelist", timeout=5)
        test_result(
            "GET /api/whitelist",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        
        # 测试添加白名单
        response = requests.post(
            f"{BASE_URL}/api/whitelist",
            data="ip=192.168.1.100",
            timeout=5
        )
        test_result(
            "POST /api/whitelist (add)",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        
        # 测试Web界面
        response = requests.get(f"{BASE_URL}/", timeout=5)
        test_result(
            "GET / (Web Interface)",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        
    except requests.exceptions.ConnectionError:
        print("\n  ✗ Web server not running at http://localhost:8080")
        print("    Please start the server with: python main.py")
        return False
    except Exception as e:
        print(f"\n  ✗ Connection error: {e}")
        return False
    
    return True


def test_waf_system():
    """测试4: 完整的WAF系统流程"""
    print("\n" + "="*70)
    print("TEST 4: Complete WAF Detection Flow")
    print("="*70)
    
    from main import WAFSystem
    
    waf = WAFSystem()
    
    # 测试各种攻击
    test_cases = [
        {
            'name': 'SQL Injection (UNION)',
            'data': {'url': '/api/user?id=1 UNION SELECT * FROM users', 'method': 'GET', 'body': ''},
            'should_block': True,
            'expected_category': 'sql_injection'
        },
        {
            'name': 'SQL Injection (OR 1=1)',
            'data': {'url': '/login', 'method': 'POST', 'body': 'user=admin&pass=" OR "1"="1'},
            'should_block': True,
            'expected_category': 'sql_injection'
        },
        {
            'name': 'XSS Attack',
            'data': {'url': '/search?q=test', 'method': 'POST', 'body': '<img src=x onerror=alert("XSS")>'},
            'should_block': True,
            'expected_category': 'xss'
        },
        {
            'name': 'Directory Traversal',
            'data': {'url': '/files?path=../../etc/passwd', 'method': 'GET', 'body': ''},
            'should_block': True,
            'expected_category': 'directory_traversal'
        },
        {
            'name': 'PHP File Upload',
            'data': {'url': '/upload', 'method': 'POST', 'body': 'file.php'},
            'should_block': True,
            'expected_category': 'malicious_file'
        },
        {
            'name': 'Normal Request 1',
            'data': {'url': '/api/users', 'method': 'GET', 'body': ''},
            'should_block': False,
            'expected_category': 'normal'
        },
        {
            'name': 'Normal Request 2',
            'data': {'url': '/home/about', 'method': 'GET', 'body': ''},
            'should_block': False,
            'expected_category': 'normal'
        }
    ]
    
    for test_case in test_cases:
        result = waf.detect_request(test_case['data'])
        
        passed = result['blocked'] == test_case['should_block']
        if test_case['should_block'] and result['category'] != test_case['expected_category']:
            passed = False
        
        message = f"Blocked: {result['blocked']}"
        if result['blocked']:
            message += f", Category: {result['category']}"
        
        test_result(test_case['name'], passed, message)


def print_summary():
    """打印测试总结"""
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    total = TEST_RESULTS['passed'] + TEST_RESULTS['failed']
    passed = TEST_RESULTS['passed']
    
    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed} ✓")
    print(f"Failed: {TEST_RESULTS['failed']} ✗")
    print(f"Success Rate: {(passed/total*100):.1f}%")
    
    if TEST_RESULTS['errors']:
        print("\nFailed Tests:")
        for error in TEST_RESULTS['errors']:
            print(f"  - {error}")
    
    print("\n" + "="*70)
    if TEST_RESULTS['failed'] == 0:
        print("✓ ALL TESTS PASSED!")
    else:
        print(f"✗ {TEST_RESULTS['failed']} TEST(S) FAILED")
    print("="*70)


if __name__ == '__main__':
    print("\n" + "="*70)
    print("DL-WAF Phase 1 - Integration Tests")
    print("="*70)
    
    # 运行所有测试
    test_rule_engine()
    test_attack_log()
    test_waf_system()
    
    # 测试Web API（需要服务器运行）
    if test_web_api():
        pass
    
    # 打印总结
    print_summary()
