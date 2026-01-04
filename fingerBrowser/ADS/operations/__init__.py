"""
ADS 浏览器操作方法模块
"""
from .get_all_browsers_info import get_all_browsers_info
from .get_single_browser_info import get_single_browser_info
from .create_new_browser import create_new_browser
from .launch_browser import launch_browser
from .close_browser import close_browser
from .delete_browser import delete_browser
from .close_all_browser import close_all_browser
from .judge_browser_working import judge_browser_working

__all__ = [
    'get_all_browsers_info',
    'get_single_browser_info',
    'create_new_browser',
    'launch_browser',
    'close_browser',
    'delete_browser',
    'close_all_browser',
    'judge_browser_working',
]
