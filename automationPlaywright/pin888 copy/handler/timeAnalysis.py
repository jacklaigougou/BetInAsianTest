"""
PIN888 平台 - 比赛时间分析
将不同运动项目的时间转换为统一的倒计时格式
"""


def analyze_remaining_time(sport_type, match_state_type):
    """
    分析比赛剩余时间,将正计时或倒计时统一转换为剩余秒数

    Args:
        sport_type: 运动类型 ("football"/"soccer" 或 "basketball")
        match_state_type: 比赛状态对象
            - 足球: {"matchPhase": "FirstHalf", "elapsed": "00:28:01"}
            - 篮球: {"matchPhase": "...", "elapsed": {...}} 或直接是 elapsed 对象

    Returns:
        dict: {
            'match_phase': str,        # 比赛阶段
            'remaining_seconds': int   # 剩余秒数
        }
        None: 解析失败

    Examples:
        # 足球
        >>> analyze_remaining_time("football", {
                "matchPhase": "FirstHalf",
                "elapsed": "00:28:01"
            })
        {'match_phase': 'FirstHalf', 'remaining_seconds': 1079}

        # 篮球
        >>> analyze_remaining_time("basketball", {
                "matchPhase": "...",
                "elapsed": {
                    "currentQuarter": 2,
                    "quarterMinutesRemaining": 3,
                    "quarterSecondsRemaining": 19
                }
            })
        {'match_phase': 'Quarter2', 'remaining_seconds': 199}
    """
    try:
        if not match_state_type:
            print(f"❌ [时间分析] match_state_type 为空")
            return None

        sport_lower = sport_type.lower()

        # ==================== 足球 ====================
        if sport_lower in ['football', 'soccer']:
            # 足球格式: {"matchPhase": "FirstHalf", "elapsed": "00:28:01"}
            match_phase = match_state_type.get('matchPhase', '')
            elapsed = match_state_type.get('elapsed', '')

            if not elapsed:
                print(f"❌ [足球时间] elapsed 为空")
                return None

            return _analyze_football_time(match_phase, elapsed)

        # ==================== 篮球 ====================
        elif sport_lower == 'basketball':
            # 篮球格式: 直接是倒计时对象,没有 elapsed 包装
            # {"currentQuarter": 3, "quarterMinutesRemaining": 4, "quarterSecondsRemaining": 57}
            return _analyze_basketball_time(match_state_type)

        else:
            print(f"❌ [时间分析] 不支持的运动类型: {sport_type}")
            return None

    except Exception as e:
        print(f"❌ [时间分析] 解析失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def _analyze_football_time(match_phase, elapsed):
    """
    足球时间分析 (正计时 → 倒计时)

    足球规则:
    - 上半场: 45分钟
    - 下半场: 45分钟
    - elapsed 格式: "00:28:01" (HH:MM:SS)
    """
    # 每半场时长 (秒)
    HALF_DURATION = 45 * 60  # 2700秒

    # 解析已过时间
    try:
        time_parts = elapsed.split(':')
        hours = int(time_parts[0]) if len(time_parts) > 2 else 0
        minutes = int(time_parts[-2])
        seconds = int(time_parts[-1])
        elapsed_seconds = hours * 3600 + minutes * 60 + seconds
    except (ValueError, IndexError) as e:
        print(f"❌ [足球时间] 解析 elapsed 失败: {elapsed}, 错误: {e}")
        return None

    # 确定比赛阶段
    phase_lower = match_phase.lower()

    if 'first' in phase_lower or phase_lower == '1h':
        # 上半场
        period_remaining = max(0, HALF_DURATION - elapsed_seconds)
        total_remaining = period_remaining + HALF_DURATION  # 上半场剩余 + 下半场全部
        phase_name = "FirstHalf"

    elif 'second' in phase_lower or phase_lower == '2h':
        # 下半场
        period_remaining = max(0, HALF_DURATION - elapsed_seconds)
        total_remaining = period_remaining
        phase_name = "SecondHalf"

    else:
        print(f"❌ [足球时间] 无法识别的阶段: {match_phase}")
        return None

    return {
        'match_phase': phase_name,
        'remaining_seconds': period_remaining
    }


def _analyze_basketball_time(elapsed_data):
    """
    篮球时间分析 (倒计时)

    篮球规则:
    - 每节: 10分钟 (NBA 12分钟)
    - 共4节
    - elapsed_data 格式: {
          "currentQuarter": 3,
          "quarterMinutesRemaining": 4,
          "quarterSecondsRemaining": 57
      }
    """
    # 提取当前节数
    current_quarter = elapsed_data.get('currentQuarter', 1)

    # 提取剩余时间
    minutes_remaining = elapsed_data.get('quarterMinutesRemaining', 0)
    seconds_remaining = elapsed_data.get('quarterSecondsRemaining', 0)

    # 当前节剩余秒数
    period_remaining = minutes_remaining * 60 + seconds_remaining

    return {
        'match_phase': f"Quarter{current_quarter}",
        'remaining_seconds': period_remaining
    }


# ==================== 测试代码 ====================
if __name__ == "__main__":
    print("=== 足球测试 ===")

    # 测试1: 足球上半场 28:01
    result1 = analyze_remaining_time("football", {
        "matchPhase": "FirstHalf",
        "elapsed": "00:28:01"
    })
    print(f"上半场 28:01 → {result1}")
    # 预期: {'match_phase': 'FirstHalf', 'remaining_seconds': 1079}

    # 测试2: 足球下半场 40:30
    result2 = analyze_remaining_time("football", {
        "matchPhase": "SecondHalf",
        "elapsed": "00:40:30"
    })
    print(f"下半场 40:30 → {result2}")
    # 预期: {'match_phase': 'SecondHalf', 'remaining_seconds': 270}

    print("\n=== 篮球测试 ===")

    # 测试3: 篮球第2节剩余 3:19
    result3 = analyze_remaining_time("basketball", {
        "currentQuarter": 2,
        "quarterMinutesRemaining": 3,
        "quarterSecondsRemaining": 19
    })
    print(f"第2节剩余 3:19 → {result3}")
    # 预期: {'match_phase': 'Quarter2', 'remaining_seconds': 199}

    # 测试4: 篮球第4节剩余 1:05
    result4 = analyze_remaining_time("basketball", {
        "currentQuarter": 4,
        "quarterMinutesRemaining": 1,
        "quarterSecondsRemaining": 5
    })
    print(f"第4节剩余 1:05 → {result4}")
    # 预期: {'match_phase': 'Quarter4', 'remaining_seconds': 65}

    # 测试5: 你的实际数据
    result5 = analyze_remaining_time("basketball", {
        "currentQuarter": 3,
        "quarterMinutesRemaining": 4,
        "quarterSecondsRemaining": 57
    })
    print(f"第3节剩余 4:57 → {result5}")
    # 预期: {'match_phase': 'Quarter3', 'remaining_seconds': 297}
