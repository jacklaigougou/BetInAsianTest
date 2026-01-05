# -*- coding: utf-8 -*-
"""
JS 加载器初始化示例

在程序启动时调用此函数,预加载所有平台的 JS 文件
"""
from utils import get_js_loader
from configs.settings import Settings


def initialize_js_loader():
    """
    初始化 JS 加载器,加载所有平台的 JS 文件

    使用方式:
        在 main.py 或程序入口处调用:

        from utils.init_js_loader import initialize_js_loader

        # 程序启动时
        initialize_js_loader()
    """
    print("🔧 初始化 JS 加载器...")

    js_loader = get_js_loader()
    settings = Settings()

    total_files = 0

    # 遍历所有平台配置
    for platform_name, platform_config in settings.PLATFORM_INFO.items():
        js_base_path = platform_config.get('js_base_path')

        if js_base_path:
            print(f"\n📦 加载 {platform_name} 平台的 JS 文件...")
            count = js_loader.load_platform_js(platform_name, js_base_path)

            if count > 0:
                print(f"  ✅ {platform_name}: {count} 个文件")
                total_files += count
            else:
                print(f"  ⚠️ {platform_name}: 未找到 JS 文件")
        else:
            print(f"  ⚠️ {platform_name}: 未配置 js_base_path")

    print(f"\n✅ JS 加载器初始化完成! 共加载 {total_files} 个文件")
    print(f"📊 加载统计: {js_loader.get_stats()}")

    return js_loader


if __name__ == "__main__":
    # 测试加载
    initialize_js_loader()
