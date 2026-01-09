from typing import Dict, Optional


class SportsbetMarketGroups:
    """
    Sportsbet Market Groups cache singleton
    Cache {sport: {group_name: group_id}} mapping

    虽然同名 marketGroup 的 ID 是全局唯一的,
    但不同运动类型可能有不同的 marketGroup 类型(如篮球有 Quarter,足球有 Half),
    所以按 sport 分类存储
    """
    _instance: Optional['SportsbetMarketGroups'] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not SportsbetMarketGroups._initialized:
            # {sport: {group_name: group_id}}
            self._market_groups_cache: Dict[str, Dict[str, str]] = {}
            SportsbetMarketGroups._initialized = True

    def get_group_id(self, sport: str, group_name: str) -> Optional[str]:
        """
        通过组名获取 group_id

        Args:
            sport: 运动类型 (如 'basketball', 'soccer')
            group_name: 组名 (如 "All", "Popular", "Game Lines" 等)

        Returns:
            group_id 或 None
        """
        if sport not in self._market_groups_cache:
            return None

        group_id = self._market_groups_cache[sport].get(group_name)
        if group_id:
            print(f"[缓存] 找到 {sport} marketGroup '{group_name}' -> '{group_id}'")
        return group_id

    def update_groups(self, sport: str, market_groups: list):
        """
        更新缓存中的 marketGroups 映射

        Args:
            sport: 运动类型 (如 'basketball', 'soccer')
            market_groups: GraphQL 响应中的 marketGroups 列表
        """
        if not market_groups:
            return

        if sport not in self._market_groups_cache:
            self._market_groups_cache[sport] = {}

        for group in market_groups:
            group_name = group.get('name') or group.get('enName')
            group_id = group.get('id')

            if group_name and group_id:
                # 如果是新的映射,添加到缓存
                if group_name not in self._market_groups_cache[sport]:
                    self._market_groups_cache[sport][group_name] = group_id
                    print(f"[缓存] 添加 {sport} marketGroup: '{group_name}' -> '{group_id}'")

    def clear_cache(self):
        """清空缓存"""
        self._market_groups_cache.clear()
        print(f"[缓存] marketGroups 缓存已清空")


# 创建全局单例实例
sportsbet_market_groups = SportsbetMarketGroups()
