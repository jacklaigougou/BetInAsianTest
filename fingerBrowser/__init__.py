"""
FingerBrowser 指纹浏览器统一接口
支持 Linken Sphere, ADS 等多种指纹浏览器
"""
from .fingerBrowser import FingerBrowser
from .interface import FingerBrowserBase

__all__ = ["FingerBrowser", "FingerBrowserBase"]
__version__ = "0.1.0"
