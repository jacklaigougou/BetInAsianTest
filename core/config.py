"""
核心配置单例类

用于存储全局配置参数,确保整个应用程序使用统一的配置
"""


class Config:
    """
    配置单例类

    使用单例模式确保全局只有一个配置实例,
    所有模块共享同一份配置参数

    Example:
        >>> config = Config()
        >>> config.ODDS_DROP_THRESHOLD
        10.0
        >>> config.ODDS_DROP_THRESHOLD = 15.0
        >>> Config().ODDS_DROP_THRESHOLD
        15.0
    """

    _instance = None

    def __new__(cls):
        """
        单例模式实现:确保只创建一个实例

        Returns:
            Config: 配置实例
        """
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """
        初始化配置参数(只执行一次)
        """
        if self._initialized:
            return

        # ==================== 套利配置 ====================

        # 赔率下降阈值(百分比)
        # 当赔率下降超过此阈值时,补单流程会等待更好的赔率
        # 例如: 10.0 表示赔率下降超过 10% 时会继续等待
        self.ODDS_DROP_THRESHOLD = 10.0

        # 补单超时时间(秒)
        # 补单流程中 while 循环的最大执行时间
        # 超过此时间后,即使赔率仍在下降也会停止等待
        self.SUPPLEMENTARY_ORDER_TIMEOUT = 60.0

        # 补单最大重试次数
        # 当补单失败后,最多重试的次数
        # 例如: 3 表示最多重试 3 次
        self.MAX_RETRY_COUNT = 10

        # ==================== 其他配置 ====================
        # 可以在这里添加更多配置参数
        self.ENABLE_AUTO_MONITOR = True
        self._initialized = True


        # 是否正在循环中的判断开关
        # self.PIN888_CYCLEING = True


    def set_odds_drop_threshold(self, value: float):
        """
        设置赔率下降阈值

        Args:
            value: 阈值百分比,例如 10.0 表示 10%

        Example:
            >>> config = Config()
            >>> config.set_odds_drop_threshold(15.0)
        """
        if not isinstance(value, (int, float)) or value < 0:
            raise ValueError(f"ODDS_DROP_THRESHOLD 必须是非负数,收到: {value}")

        self.ODDS_DROP_THRESHOLD = float(value)
        print(f"✅ [配置更新] ODDS_DROP_THRESHOLD 已设置为 {self.ODDS_DROP_THRESHOLD}%")

    def get_odds_drop_threshold(self) -> float:
        """
        获取赔率下降阈值

        Returns:
            float: 阈值百分比

        Example:
            >>> config = Config()
            >>> config.get_odds_drop_threshold()
            10.0
        """
        return self.ODDS_DROP_THRESHOLD

    def set_supplementary_order_timeout(self, value: float):
        """
        设置补单超时时间

        Args:
            value: 超时时间(秒),例如 60.0 表示 60 秒

        Example:
            >>> config = Config()
            >>> config.set_supplementary_order_timeout(90.0)
        """
        if not isinstance(value, (int, float)) or value <= 0:
            raise ValueError(f"SUPPLEMENTARY_ORDER_TIMEOUT 必须是正数,收到: {value}")

        self.SUPPLEMENTARY_ORDER_TIMEOUT = float(value)
        print(f"✅ [配置更新] SUPPLEMENTARY_ORDER_TIMEOUT 已设置为 {self.SUPPLEMENTARY_ORDER_TIMEOUT} 秒")

    def get_supplementary_order_timeout(self) -> float:
        """
        获取补单超时时间

        Returns:
            float: 超时时间(秒)

        Example:
            >>> config = Config()
            >>> config.get_supplementary_order_timeout()
            60.0
        """
        return self.SUPPLEMENTARY_ORDER_TIMEOUT

    def set_max_retry_count(self, value: int):
        """
        设置最大重试次数

        Args:
            value: 最大重试次数,例如 3 表示最多重试 3 次

        Example:
            >>> config = Config()
            >>> config.set_max_retry_count(5)
        """
        if not isinstance(value, int) or value < 0:
            raise ValueError(f"MAX_RETRY_COUNT 必须是非负整数,收到: {value}")

        self.MAX_RETRY_COUNT = int(value)
        print(f"✅ [配置更新] MAX_RETRY_COUNT 已设置为 {self.MAX_RETRY_COUNT} 次")

    def get_max_retry_count(self) -> int:
        """
        获取最大重试次数

        Returns:
            int: 最大重试次数

        Example:
            >>> config = Config()
            >>> config.get_max_retry_count()
            3
        """
        return self.MAX_RETRY_COUNT

    def __repr__(self):
        """
        返回配置的字符串表示

        Returns:
            str: 配置信息
        """
        return (
            f"Config("
            f"ODDS_DROP_THRESHOLD={self.ODDS_DROP_THRESHOLD}%, "
            f"SUPPLEMENTARY_ORDER_TIMEOUT={self.SUPPLEMENTARY_ORDER_TIMEOUT}s, "
            f"MAX_RETRY_COUNT={self.MAX_RETRY_COUNT}"
            f")"
        )


# 创建全局单例实例,方便直接导入使用
config = Config()
