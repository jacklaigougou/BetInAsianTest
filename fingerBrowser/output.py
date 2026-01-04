"""
返回值验证装饰器
每个验证器与对应的函数名称一致
"""
import functools
import logging
from typing import Callable

logger = logging.getLogger(__name__)


def validate_get_all_browsers_info(func: Callable) -> Callable:
    """
    验证 get_all_browsers_info 返回值

    严格检查:
    - 返回值必须是列表
    - 列表中每个元素必须是字典
    - 每个字典必须包含以下字段(可以为空值):
      * handler_name: 浏览器名称
      * uuid: 完整UUID
      * id: 短ID
      * status: 运行状态
    """
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        result = await func(self, *args, **kwargs)

        # 1. 验证返回值类型
        if not isinstance(result, list):
            logger.error(f"{func.__name__} 返回值不是列表类型: {type(result)}")
            raise TypeError(f"期望返回列表,实际返回: {type(result)}")

        # 2. 验证列表中的每个元素
        required_fields = ['handler_name', 'uuid', 'id', 'status']

        for i, item in enumerate(result):
            # 2.1 验证元素类型
            if not isinstance(item, dict):
                logger.error(f"{func.__name__} 列表第 {i} 项不是字典类型: {type(item)}")
                raise TypeError(f"列表第 {i} 项期望字典,实际: {type(item)}")

            # 2.2 验证必需字段
            missing_fields = [field for field in required_fields if field not in item]
            if missing_fields:
                logger.error(
                    f"{func.__name__} 列表第 {i} 项缺少必需字段: {missing_fields}\n"
                    f"   数据项: {item}"
                )
                raise ValueError(
                    f"列表第 {i} 项缺少必需字段: {missing_fields}\n"
                    f"   必需字段: {required_fields}\n"
                    f"   实际字段: {list(item.keys())}"
                )

        logger.debug(f"{func.__name__} 列表验证通过,共 {len(result)} 项")
        return result

    return wrapper


def validate_get_single_browser_info(func: Callable) -> Callable:
    """
    验证 get_single_browser_info 返回值

    严格检查:
    - 返回值必须是字典
    - 必须包含以下字段(可以为空值):
      * uuid: 完整UUID
      * id: 短ID
      * handler_name: 浏览器名称
      * debug_port: 调试端口
      * ws_url: WebSocket连接地址
    """
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        result = await func(self, *args, **kwargs)

        # 1. 验证返回值类型
        if not isinstance(result, dict):
            logger.error(f"{func.__name__} 返回值不是字典类型: {type(result)}")
            raise TypeError(f"期望返回字典,实际返回: {type(result)}")

        # 2. 验证必需字段
        required_fields = ['uuid', 'id', 'handler_name', 'debug_port', 'ws_url']
        missing_fields = [field for field in required_fields if field not in result]

        if missing_fields:
            logger.error(
                f"{func.__name__} 返回值缺少必需字段: {missing_fields}\n"
                f"   数据: {result}"
            )
            raise ValueError(
                f"返回值缺少必需字段: {missing_fields}\n"
                f"   必需字段: {required_fields}\n"
                f"   实际字段: {list(result.keys())}"
            )

        logger.debug(f"{func.__name__} 返回值验证通过")
        return result

    return wrapper


def validate_create_new_browser(func: Callable) -> Callable:
    """
    验证 create_new_browser 返回值

    严格检查:
    - 返回值必须是字典
    - 必须包含以下字段(可以为空值):
      * handler_name: 浏览器名称
      * uuid: 完整UUID
      * id: 短ID
      * status: 运行状态
      * success: 创建是否成功 (布尔值)
    """
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        result = await func(self, *args, **kwargs)

        # 1. 验证返回值类型
        if not isinstance(result, dict):
            logger.error(f"{func.__name__} 返回值不是字典类型: {type(result)}")
            raise TypeError(f"期望返回字典,实际返回: {type(result)}")

        # 2. 验证必需字段
        required_fields = ['handler_name', 'uuid', 'id', 'status', 'success']
        missing_fields = [field for field in required_fields if field not in result]

        if missing_fields:
            logger.error(
                f"{func.__name__} 返回值缺少必需字段: {missing_fields}\n"
                f"   数据: {result}"
            )
            raise ValueError(
                f"返回值缺少必需字段: {missing_fields}\n"
                f"   必需字段: {required_fields}\n"
                f"   实际字段: {list(result.keys())}"
            )

        logger.debug(f"{func.__name__} 创建结果验证通过")
        return result

    return wrapper


def validate_launch_browser(func: Callable) -> Callable:
    """
    验证 launch_browser 返回值

    严格检查:
    - 返回值必须是字典
    - 必须包含以下字段(可以为空值):
      * uuid: 完整UUID
      * debug_port: 调试端口
      * success: 启动是否成功 (布尔值)
    """
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        result = await func(self, *args, **kwargs)

        # 1. 验证返回值类型
        if not isinstance(result, dict):
            logger.error(f"{func.__name__} 返回值不是字典类型: {type(result)}")
            raise TypeError(f"期望返回字典,实际返回: {type(result)}")

        # 2. 验证必需字段
        required_fields = ['uuid', 'debug_port', 'success']
        missing_fields = [field for field in required_fields if field not in result]

        if missing_fields:
            logger.error(
                f"{func.__name__} 返回值缺少必需字段: {missing_fields}\n"
                f"   数据: {result}"
            )
            raise ValueError(
                f"返回值缺少必需字段: {missing_fields}\n"
                f"   必需字段: {required_fields}\n"
                f"   实际字段: {list(result.keys())}"
            )

        logger.debug(f"{func.__name__} 启动结果验证通过")
        return result

    return wrapper


def validate_close_browser(func: Callable) -> Callable:
    """
    验证 close_browser 返回值

    检查:
    - 返回值必须是布尔类型
    """
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        result = await func(self, *args, **kwargs)

        if not isinstance(result, bool):
            logger.warning(f"{func.__name__} 返回值不是布尔类型: {type(result)}, 尝试转换")
            # 尝试转换为布尔值
            return bool(result)

        logger.debug(f"{func.__name__} 返回布尔值: {result}")
        return result

    return wrapper


def validate_delete_browser(func: Callable) -> Callable:
    """
    验证 delete_browser 返回值

    检查:
    - 返回值必须是布尔类型
    """
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        result = await func(self, *args, **kwargs)

        if not isinstance(result, bool):
            logger.warning(f"{func.__name__} 返回值不是布尔类型: {type(result)}, 尝试转换")
            # 尝试转换为布尔值
            return bool(result)

        logger.debug(f"{func.__name__} 返回布尔值: {result}")
        return result

    return wrapper


def validate_close_all_browser(func: Callable) -> Callable:
    """
    验证 close_all_browser 返回值

    检查:
    - 返回值必须是字典
    - 必须包含字段: total, closed, failed, details
    """
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        result = await func(self, *args, **kwargs)

        # 1. 验证返回值类型
        if not isinstance(result, dict):
            logger.error(f"{func.__name__} 返回值不是字典类型: {type(result)}")
            raise TypeError(f"期望返回字典,实际返回: {type(result)}")

        # 2. 验证必需字段
        required_fields = ['total', 'closed', 'failed', 'details']
        missing_fields = [field for field in required_fields if field not in result]

        if missing_fields:
            logger.error(
                f"{func.__name__} 返回值缺少必需字段: {missing_fields}\n"
                f"   数据: {result}"
            )
            raise ValueError(
                f"返回值缺少必需字段: {missing_fields}\n"
                f"   必需字段: {required_fields}\n"
                f"   实际字段: {list(result.keys())}"
            )

        logger.debug(f"{func.__name__} 返回值验证通过")
        return result

    return wrapper


__all__ = [
    'validate_get_all_browsers_info',
    'validate_get_single_browser_info',
    'validate_create_new_browser',
    'validate_launch_browser',
    'validate_close_browser',
    'validate_delete_browser',
    'validate_close_all_browser',
]
