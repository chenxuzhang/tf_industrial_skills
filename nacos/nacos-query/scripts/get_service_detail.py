#!/usr/bin/env python3
"""获取Nacos服务详情"""
import sys
import json
import argparse
from scripts.config import NacosConfig
from scripts.nacos_client import NacosClient

def main():
    parser = argparse.ArgumentParser(description='获取Nacos服务详情')
    parser.add_argument('--env', required=True, choices=['test', 'staging', 'prod'], help='目标环境')
    parser.add_argument('--service-name', required=True, help='服务名称')
    parser.add_argument('--group', help='分组名称')
    parser.add_argument('--namespace', help='命名空间ID')
    parser.add_argument('--config', help='配置文件路径')
    args = parser.parse_args()
    
    try:
        config = NacosConfig.load(args.env, args.config)
        client = NacosClient(config)
        result = client.get_service_detail(
            service_name=args.service_name,
            group_name=args.group,
            namespace_id=args.namespace
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0 if result.get('code') == 200 else 1)
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False))
        sys.exit(1)

if __name__ == '__main__':
    main()
