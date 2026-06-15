import time
import base64
import logging
from typing import Any, Dict, Optional
import requests
from scripts.config import NacosConfig

logger = logging.getLogger(__name__)

class NacosClient:
    """Client for Nacos REST API."""
    
    def __init__(self, config: NacosConfig):
        """Initialize Nacos client.
        
        Args:
            config: Nacos connection configuration
        """
        self.config = config
        self.session = requests.Session()
        self.token = None
        
        self.session.headers.update({
            "Accept": "application/json",
        })
        
        # Try to get auth token for Nacos 2.x
        if config.username and config.password:
            self._login()
    
    def _login(self):
        """Login to Nacos and get access token."""
        try:
            url = f"{self.config.server_addr.rstrip('/')}/nacos/v1/auth/login"
            response = requests.post(url, data={
                "username": self.config.username,
                "password": self.config.password,
            }, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("accessToken"):
                    self.token = data["accessToken"]
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.token}"
                    })
        except Exception as e:
            logger.debug(f"Login failed (non-critical): {e}")
    
    def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path
            **kwargs: Additional arguments for requests
            
        Returns:
            Response data as dictionary
        """
        url = f"{self.config.server_addr.rstrip('/')}{path}"
        kwargs.setdefault("timeout", (self.config.connection_timeout / 1000, 
                                       self.config.read_timeout / 1000))
        
        last_exception = None
        for attempt in range(self.config.max_retries):
            try:
                logger.debug(f"Calling Nacos API [{path}], attempt {attempt + 1}/{self.config.max_retries}")
                response = self.session.request(method, url, **kwargs)
                response.raise_for_status()
                return self._parse_response(response)
            except Exception as e:
                last_exception = e
                logger.warning(f"Nacos API [{path}] attempt {attempt + 1}/{self.config.max_retries} failed: {e}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_backoff * (2 ** attempt) / 1000)
        
        raise RuntimeError(f"Nacos API [{path}] failed after {self.config.max_retries} attempts: {last_exception}")
    
    def _parse_response(self, response: requests.Response) -> Dict[str, Any]:
        """Parse API response.
        
        Args:
            response: HTTP response object
            
        Returns:
            Parsed response data
        """
        try:
            data = response.json()
            if "code" in data:
                if data["code"] != 200:
                    return {
                        "code": data["code"],
                        "message": data.get("message", "Unknown error"),
                        "data": None,
                    }
                return {"code": 200, "data": data.get("data")}
            return {"code": 200, "data": data}
        except ValueError:
            # Response is plain text (e.g., config content)
            return {"code": 200, "data": response.text}
    
    def get_namespaces(self) -> Dict[str, Any]:
        """Get list of namespaces.
        
        Returns:
            Dictionary with namespace list
        """
        return self._request("GET", "/nacos/v1/console/namespaces")
    
    def get_config_list(self, namespace_id: str = "public") -> Dict[str, Any]:
        """Get list of configurations in a namespace.
        
        Args:
            namespace_id: Namespace ID (default: public)
            
        Returns:
            Dictionary with configuration list
        """
        params = {
            "dataId": "",
            "group": "",
            "tenant": namespace_id,
            "pageNo": 1,
            "pageSize": 500,
            "search": "blur",
        }
        return self._request("GET", "/nacos/v1/cs/configs", params=params)
    
    def get_config_content(self, data_id: str, group: str = "DEFAULT_GROUP", 
                          namespace_id: str = "public") -> Dict[str, Any]:
        """Get configuration content.
        
        Args:
            data_id: Configuration ID
            group: Configuration group
            namespace_id: Namespace ID
            
        Returns:
            Dictionary with configuration content
        """
        params = {
            "dataId": data_id,
            "group": group,
            "tenant": namespace_id,
        }
        return self._request("GET", "/nacos/v1/cs/configs", params=params)
    
    def get_services(self, namespace_id: Optional[str] = None, 
                    group_name: Optional[str] = None,
                    page_no: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """Get list of services.
        
        Args:
            namespace_id: Namespace ID
            group_name: Group name
            page_no: Page number
            page_size: Page size
            
        Returns:
            Dictionary with service list
        """
        params = {
            "pageNo": page_no,
            "pageSize": page_size,
        }
        if namespace_id:
            params["tenant"] = namespace_id
        if group_name:
            params["groupName"] = group_name
        
        return self._request("GET", "/nacos/v1/ns/service/list", params=params)
    
    def get_service_detail(self, service_name: str, 
                          group_name: Optional[str] = None,
                          namespace_id: Optional[str] = None) -> Dict[str, Any]:
        """Get service detail.
        
        Args:
            service_name: Service name
            group_name: Group name
            namespace_id: Namespace ID
            
        Returns:
            Dictionary with service detail
        """
        # 获取服务基本信息
        params = {"serviceName": service_name}
        if group_name:
            params["groupName"] = group_name
        if namespace_id:
            params["tenant"] = namespace_id
        
        service_info = self._request("GET", "/nacos/v1/ns/service", params=params)
        
        # 获取实例列表
        instance_params = {
            "serviceName": service_name,
            "clusterName": "DEFAULT",
            "pageNo": 1,
            "pageSize": 100,
        }
        if group_name:
            instance_params["groupName"] = group_name
        if namespace_id:
            instance_params["namespaceId"] = namespace_id
        
        instances = self._request("GET", "/nacos/v1/ns/catalog/instances", params=instance_params)
        
        # 合并结果
        if service_info.get("code") == 200:
            result = service_info["data"]
            # 修正 namespaceId（API 返回的可能是 public）
            if namespace_id:
                result["namespaceId"] = namespace_id
            if instances.get("code") == 200:
                result["instances"] = instances["data"].get("list", [])
                result["instanceCount"] = instances["data"].get("count", 0)
            return {"code": 200, "data": result}
        
        return service_info
