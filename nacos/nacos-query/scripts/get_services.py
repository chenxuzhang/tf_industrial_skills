#!/usr/bin/env python3
"""获取Nacos服务列表"""
import sys
import json
import argparse
from scripts.config import NacosConfig
from scripts.nacos_client import NacosClient

def main():
    parser = argparse.ArgumentParser(description='获取Nacos服务列表')
    parser.add_argument('--env', required=True, choices=['test', 'staging', 'prod'], help='目标环境')
    parser.add_argument('--namespace', help='命名空间ID')
    parser.add_argument('--group', help='分组名称')
    parser.add_argument('--page-no', type=int, default=1, help='页码 (默认: 1)')
    parser.add_argument('--page-size', type=int, default=10, help='每页数量 (默认: 10)')
    parser.add_argument('--config', help='配置文件路径')
    args = parser.parse_args()
    
    try:
        config = NacosConfig.load(args.env, args.config)
        client = NacosClient(config)
        result = client.get_services(
            namespace_id=args.namespace,
            group_name=args.group,
            page_no=args.page_no,
            page_size=args.page_size
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0 if result.get('code') == 200 else 1)
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False))
        sys.exit(1)

if __name__ == '__main__':
    main()
