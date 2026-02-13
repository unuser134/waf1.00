"""
Web工具函数 - 请求解析、响应生成等
"""
import re
from typing import Dict, Any, Tuple, List
from urllib.parse import urlparse, parse_qs, parse_qsl, unquote, urlencode
import json


class HTTPRequestParser:
    """HTTP请求解析器"""
    
    @staticmethod
    def parse_request(request_string: str) -> Dict[str, Any]:
        """
        解析HTTP请求
        
        Args:
            request_string: HTTP请求原始字符串
            
        Returns:
            解析后的请求字典
        """
        lines = request_string.strip().split('\n')
        
        # 解析请求行
        request_line = lines[0].strip()
        parts = request_line.split()
        
        request = {
            'method': parts[0] if len(parts) > 0 else 'GET',
            'url': parts[1] if len(parts) > 1 else '/',
            'version': parts[2] if len(parts) > 2 else 'HTTP/1.1',
            'headers': {},
            'body': ''
        }
        
        # 解析请求头和body
        header_end = 1
        for i in range(1, len(lines)):
            line = lines[i].strip()
            if line == '':
                header_end = i + 1
                break
            
            if ':' in line:
                key, value = line.split(':', 1)
                request['headers'][key.strip()] = value.strip()
        
        # 解析body
        if header_end < len(lines):
            request['body'] = '\n'.join(lines[header_end:])
        
        # 解析URL
        parsed_url = urlparse(request['url'])
        request['path'] = parsed_url.path
        request['query_string'] = parsed_url.query
        request['query_params'] = parse_qs(parsed_url.query)
        
        return request
    
    @staticmethod
    def get_form_data(body: str, content_type: str = '') -> Dict[str, Any]:
        """
        解析表单数据
        
        Args:
            body: 请求体
            content_type: Content-Type头
            
        Returns:
            解析后的表单数据
        """
        if 'application/json' in content_type:
            try:
                return json.loads(body)
            except:
                return {}
        
        elif 'application/x-www-form-urlencoded' in content_type:
            data = {}
            for pair in body.split('&'):
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    data[key] = unquote(value)
            return data
        
        return {}

    @staticmethod
    def normalize_request(request: Dict[str, Any]) -> Dict[str, Any]:
        """对请求做统一规范化，减少规则重复覆盖。"""
        url = request.get('url', '') or ''
        method = (request.get('method', '') or 'GET').upper()
        headers = request.get('headers', {}) or {}
        body = request.get('body', '') or ''

        # URL 解码 + 解析 + 参数排序（保持解码后的可读形态）
        decoded_url = unquote(url)
        parsed = urlparse(decoded_url)
        query_pairs = parse_qsl(parsed.query, keep_blank_values=True)
        query_pairs.sort(key=lambda x: (x[0], x[1]))
        normalized_query = '&'.join([f"{k}={v}" for k, v in query_pairs])
        normalized_url = parsed.path
        if normalized_query:
            normalized_url = f"{normalized_url}?{normalized_query}"

        # 统一大小写与空白
        normalized_body = re.sub(r'\s+', ' ', unquote(body)).strip().lower()
        normalized_headers = {str(k).lower(): str(v).strip() for k, v in headers.items()}

        return {
            'method': method,
            'url': normalized_url.lower(),
            'headers': normalized_headers,
            'body': normalized_body,
            'query_string': normalized_query.lower(),
            'path': parsed.path.lower(),
        }


class URLDecoder:
    """URL解码和编码检测"""
    
    @staticmethod
    def detect_encoding(text: str) -> Dict[str, bool]:
        """检测文本的编码类型"""
        encoding_types = {
            'url_encoded': bool(re.search(r'%[0-9a-fA-F]{2}', text)),
            'html_encoded': bool(re.search(r'&#?[a-zA-Z0-9]+;', text)),
            'hex_encoded': bool(re.search(r'\\x[0-9a-fA-F]{2}', text)),
            'base64': bool(re.match(r'^[A-Za-z0-9+/=]*$', text) and len(text) % 4 == 0),
            'unicode_encoded': bool(re.search(r'\\u[0-9a-fA-F]{4}', text))
        }
        return encoding_types
    
    @staticmethod
    def decode_all(text: str) -> Dict[str, str]:
        """尝试所有解码方式"""
        decoded = {'original': text}
        
        try:
            decoded['url_decoded'] = unquote(text)
        except:
            decoded['url_decoded'] = text
        
        # HTML实体解码
        try:
            import html
            decoded['html_decoded'] = html.unescape(text)
        except:
            decoded['html_decoded'] = text
        
        return decoded


class ContentAnalyzer:
    """内容分析"""
    
    @staticmethod
    def analyze_request(request: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析请求内容
        
        Args:
            request: 解析后的请求
            
        Returns:
            分析结果
        """
        analysis = {
            'suspicious_chars': 0,
            'encoded_content': False,
            'script_tags': 0,
            'sql_keywords': 0,
            'file_paths': 0,
            'special_chars': 0
        }
        
        # 合并所有需要检查的文本
        check_text = f"{request.get('url', '')} {request.get('body', '')}"
        
        # 统计特殊字符
        analysis['special_chars'] = len(re.findall(r'[<>\'";\\]', check_text))
        
        # 检查脚本标签
        analysis['script_tags'] = len(re.findall(r'<script|javascript:', check_text, re.I))
        
        # 检查SQL关键字
        sql_keywords = ['select', 'insert', 'update', 'delete', 'drop', 'union', 'where']
        analysis['sql_keywords'] = sum(check_text.lower().count(kw) for kw in sql_keywords)
        
        # 检查文件路径
        analysis['file_paths'] = len(re.findall(r'\.\./|\.\\\.|etc/|windows/', check_text, re.I))
        
        # 检查编码内容
        encoding_detection = URLDecoder.detect_encoding(check_text)
        analysis['encoded_content'] = any(encoding_detection.values())
        
        return analysis


class ResponseBuilder:
    """HTTP响应构建器"""
    
    @staticmethod
    def build_response(status_code: int, body: str, 
                      headers: Dict[str, str] = None, 
                      content_type: str = 'text/html') -> str:
        """
        构建HTTP响应
        
        Args:
            status_code: HTTP状态码
            body: 响应体
            headers: 额外的响应头
            content_type: Content-Type
            
        Returns:
            HTTP响应字符串
        """
        status_messages = {
            200: 'OK',
            400: 'Bad Request',
            403: 'Forbidden',
            404: 'Not Found',
            500: 'Internal Server Error'
        }
        
        status_text = status_messages.get(status_code, 'Unknown')
        response = f"HTTP/1.1 {status_code} {status_text}\r\n"
        
        # 默认响应头
        response_headers = {
            'Content-Type': content_type,
            'Content-Length': str(len(body)),
            'Server': 'DL-WAF/1.0'
        }
        
        # 添加自定义头
        if headers:
            response_headers.update(headers)
        
        for key, value in response_headers.items():
            response += f"{key}: {value}\r\n"
        
        response += "\r\n" + body
        
        return response
    
    @staticmethod
    def build_blocked_response(reason: str, rule_id: str = '') -> str:
        """构建请求被阻止的响应"""
        html_body = f"""
        <html>
        <head>
            <title>访问被拒绝</title>
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }}
                .error {{ color: #d32f2f; font-size: 24px; }}
                .reason {{ color: #666; font-size: 14px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <h1 class="error">🚨 访问被拒绝</h1>
            <p class="reason">您的请求被WAF系统阻止</p>
            <p class="reason">原因: {reason}</p>
            {f'<p class="reason">规则ID: {rule_id}</p>' if rule_id else ''}
        </body>
        </html>
        """
        
        return ResponseBuilder.build_response(403, html_body.strip())
