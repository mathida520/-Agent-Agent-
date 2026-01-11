"""
XooBay API 工具包
用于从 XooBay API 获取商品数据并转换为 AgentCard 格式
参考文档: api-geo.md
"""

import requests
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

# XooBay API 配置
XOOBAY_BASE_URL = "https://www.xoobay.com"
XOOBAY_API_KEY = "xoobay_api_ai_geo"
DEFAULT_LANG = "zh_cn"  # 默认语言：中文


class XooBayAPIError(Exception):
    """XooBay API 错误异常类"""
    pass


def get_product_info(product_id: int, lang: str = DEFAULT_LANG) -> Dict[str, Any]:
    """
    从 XooBay API 获取商品详情
    
    Args:
        product_id: 商品ID
        lang: 语言代码 (zh_cn, en, zh_hk, ru)
    
    Returns:
        商品详情数据字典
    
    Raises:
        XooBayAPIError: API 请求失败时抛出
    """
    try:
        url = f"{XOOBAY_BASE_URL}/api-geo/product-info"
        params = {
            "id": product_id,
            "lang": lang,
            "apiKey": XOOBAY_API_KEY
        }
        
        logger.info(f"请求 XooBay 商品详情: product_id={product_id}, lang={lang}")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # 检查响应状态码
        if data.get("code") != 200:
            error_msg = data.get("msg", "Unknown error")
            raise XooBayAPIError(f"XooBay API 错误: {error_msg}")
        
        return data.get("data", {})
        
    except requests.exceptions.RequestException as e:
        logger.error(f"请求 XooBay API 失败: {e}")
        raise XooBayAPIError(f"网络请求失败: {str(e)}")
    except Exception as e:
        logger.error(f"解析 XooBay API 响应失败: {e}")
        raise XooBayAPIError(f"解析响应失败: {str(e)}")


def get_store_info(store_id: int, lang: str = DEFAULT_LANG) -> Dict[str, Any]:
    """
    从 XooBay API 获取商家详情
    
    Args:
        store_id: 商家ID
        lang: 语言代码
    
    Returns:
        商家详情数据字典
    
    Raises:
        XooBayAPIError: API 请求失败时抛出
    """
    try:
        url = f"{XOOBAY_BASE_URL}/api-geo/store-info"
        params = {
            "id": store_id,
            "lang": lang,
            "apiKey": XOOBAY_API_KEY
        }
        
        logger.info(f"请求 XooBay 商家详情: store_id={store_id}, lang={lang}")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("code") != 200:
            error_msg = data.get("msg", "Unknown error")
            raise XooBayAPIError(f"XooBay API 错误: {error_msg}")
        
        return data.get("data", {})
        
    except requests.exceptions.RequestException as e:
        logger.error(f"请求 XooBay API 失败: {e}")
        raise XooBayAPIError(f"网络请求失败: {str(e)}")
    except Exception as e:
        logger.error(f"解析 XooBay API 响应失败: {e}")
        raise XooBayAPIError(f"解析响应失败: {str(e)}")


def convert_to_agent_card_format(product_data: Dict[str, Any], store_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    将 XooBay 数据格式转换为 AgentCard 数据格式
    
    Args:
        product_data: XooBay 商品数据
        store_data: XooBay 商家数据（可选）
    
    Returns:
        AgentCard 格式的数据字典
    """
    # 构建 AgentCard 数据
    agent_card_data = {
        "agentInfo": {
            "name": product_data.get("brand_name", "XOOBAY") or "XOOBAY",
            "type": "电商平台",
            "introduction": product_data.get("store_description", "XOOBAY 是全球精选购物平台，提供优质商品和便捷的购物体验。") or "XOOBAY 是全球精选购物平台，提供优质商品和便捷的购物体验。",
            "functions": [
                "商品搜索",
                "价格对比",
                "在线购买",
                "商品推荐",
                "评价查看"
            ],
            # A2A 地址格式：使用商家ID和商品ID构建
            "address": f"a2a://xoobay-agent.polyagent.ai/agent/product-{product_data.get('id', 'unknown')}"
        },
        "content": {
            "productName": product_data.get("name", ""),
            "price": f"${product_data.get('price', '0')}",
            "specifications": {
                "分类": product_data.get("category", "未分类"),
                "SKU": product_data.get("sku", "N/A"),
                "品牌": product_data.get("brand_name", "XOOBAY"),
            },
            "description": product_data.get("description", product_data.get("short_description", ""))
        },
        # Agent 能力：默认支持所有功能
        "capabilities": {
            "order": True,      # 支持下单购买
            "payment": True,    # 支持支付付款
            "logistics": True   # 支持物流配送
        },
        # Agent 性能数据：默认值
        "performance": {
            "shippingTime": "通常1-3个工作日发货，支持全球配送",
            "ratings": {
                "score": 4.5,  # 默认评分
                "count": 0,    # 默认评价数量
                "reviews": []  # 默认无评价列表
            },
            "refundPolicy": "7天无理由退货，15天内质量问题可换货，支持退款到原支付方式。"
        }
    }
    
    # 如果有商家数据，更新相关信息
    if store_data:
        store_name = store_data.get("name", "")
        if store_name:
            agent_card_data["agentInfo"]["introduction"] = store_data.get("remark", agent_card_data["agentInfo"]["introduction"])
    
    # 如果有商品图片，可以添加到规格参数中（可选）
    if product_data.get("image_url"):
        agent_card_data["content"]["imageUrl"] = product_data.get("image_url")
    
    # 如果有图库图片，可以添加（可选）
    if product_data.get("gallery_images"):
        agent_card_data["content"]["galleryImages"] = product_data.get("gallery_images")
    
    return agent_card_data


def get_agent_card_data(product_id: int, store_id: Optional[int] = None, lang: str = DEFAULT_LANG) -> Dict[str, Any]:
    """
    获取指定商品的 AgentCard 数据（完整流程）
    
    Args:
        product_id: 商品ID
        store_id: 商家ID（可选，如果不提供则从商品数据中获取）
        lang: 语言代码
    
    Returns:
        AgentCard 格式的数据字典
    
    Raises:
        XooBayAPIError: API 请求失败时抛出
    """
    try:
        # 1. 获取商品详情
        product_data = get_product_info(product_id, lang)
        
        if not product_data:
            raise XooBayAPIError(f"商品 ID {product_id} 不存在或数据为空")
        
        # 2. 获取商家详情（如果提供了商家ID，或从商品数据中获取）
        store_data = None
        if store_id:
            try:
                store_data = get_store_info(store_id, lang)
            except XooBayAPIError as e:
                logger.warning(f"获取商家详情失败，将使用默认数据: {e}")
        elif product_data.get("store_id"):
            try:
                store_data = get_store_info(product_data.get("store_id"), lang)
            except XooBayAPIError as e:
                logger.warning(f"获取商家详情失败，将使用默认数据: {e}")
        
        # 3. 转换为 AgentCard 格式
        agent_card_data = convert_to_agent_card_format(product_data, store_data)
        
        logger.info(f"成功获取商品 {product_id} 的 AgentCard 数据")
        return agent_card_data
        
    except XooBayAPIError:
        # 重新抛出 XooBayAPIError
        raise
    except Exception as e:
        logger.error(f"获取 AgentCard 数据时发生未知错误: {e}")
        raise XooBayAPIError(f"处理数据时发生错误: {str(e)}")
