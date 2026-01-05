"""
Configuration Settings
"""
import os



class Settings:
    """Global configuration settings"""

    # ==================== WebSocket Configuration ====================
    WS_HOST = os.getenv('WS_HOST', '127.0.0.1')
    WS_PORT = int(os.getenv('WS_PORT', 8765))
    WS_RECONNECT_DELAY = 5  # seconds

    # ==================== Heartbeat Configuration ====================
    HEARTBEAT_INTERVAL = 3  # seconds

    # ==================== Auto Monitor Configuration ====================
    ENABLE_AUTO_MONITOR = False  # 是否启用自动监控

    # ********************* 平台信息 *********************
    # BASE_DIR 指向项目根目录
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # AUTOMATION_DIR 指向 automationPlaywright 文件夹
    _AUTOMATION_DIR = os.path.join(_BASE_DIR, "automationPlaywright")
    
    
    
    
    PLATFORM_INFO = {
        'betinasian':{
            'platform_name': 'betinasian',
            'match_url':'betinasia.com',
            'start_url': 'https://black.betinasia.com/sportsbook/basketball?group=in+running',
            'folder_addr': 'src.automation.betinasian',   # 文件夹地址
            'file_name': 'betinasian_automation',  # 文件名
            'class_name': 'BetInAsianAutomation',  # 类名

            # * 由于不是import ,而是通过读取文件,所以会慢一点.
            'js_base_path': os.path.join(_AUTOMATION_DIR,  "betinasian", "jsCode")
        },
        'pin888': {
            'platform_name': 'pin888',
            'match_url':'pin880.com',
            'start_url': 'https://www.pin880.com/en/standard/soccer/live',
            'folder_addr': 'src.automation.pin888',  # 文件夹地址
            'file_name': 'pin888_automation',  # 文件名
            'class_name': 'Pin888Automation',  # 类名
            'js_base_path': os.path.join(_AUTOMATION_DIR, "pin888", "jsCode")
        }
    }

    # ==================== Logging Configuration ====================
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

    # ==================== 后端请求: API ====================
    BASE_URL = 'https://www.3tigerssmallgoal.com'

    