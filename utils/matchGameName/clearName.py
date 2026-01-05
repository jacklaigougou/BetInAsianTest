# -*- coding: utf-8 -*-
"""
球队名称清洗和标准化模块
"""
import re
import json
import os
from typing import List, Dict, Set


# ==================== 模块初始化: 加载配置 ====================

def _load_rules() -> Dict:
    """加载规则文件(模块加载时执行一次)"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        rules_path = os.path.join(current_dir, '..', '..', 'configs', 'team_name_rules.json')
        rules_path = os.path.normpath(rules_path)

        with open(rules_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"警告: 加载规则文件失败: {e}, 使用空规则")
        return {"stopwords": {}, "synonyms": {}, "preserve_words": []}


# 模块级别的全局变量(只加载一次)
_RULES = _load_rules()

# 构建停用词集合
_STOPWORDS: Set[str] = set()
for category, words in _RULES.get('stopwords', {}).items():
    if isinstance(words, list):
        _STOPWORDS.update(word.lower() for word in words)

# 同义词映射表
_SYNONYMS: Dict[str, str] = {
    k.lower(): v.lower()
    for k, v in _RULES.get('synonyms', {}).items()
}

# 保留词集合
_PRESERVE_WORDS: Set[str] = {
    word.lower() for word in _RULES.get('preserve_words', [])
}


# ==================== 辅助函数 ====================

def _basic_clean(name: str) -> str:
    """
        基础清理(移除括号、特殊符号等)

        Args:
            name: 原始名称

        Returns:
            str: 清理后的名称
    """
    # 移除各种括号及括号内的内容
    cleaned = re.sub(r'\([^)]*\)', '', name)
    cleaned = re.sub(r'\[[^\]]*\]', '', cleaned)
    cleaned = re.sub(r'\{[^}]*\}', '', cleaned)
    cleaned = re.sub(r'<[^>]*>', '', cleaned)

    # 移除引号类字符
    cleaned = cleaned.replace('"', '').replace("'", '').replace('`', '')

    # 将特殊符号替换为空格(保留分词边界)
    for char in '.,-_/&+*#@|~–—\\':
        cleaned = cleaned.replace(char, ' ')

    # 合并多个空格为一个
    cleaned = re.sub(r'\s+', ' ', cleaned)

    return cleaned.strip()


def _tokenize(name: str) -> List[str]:
    """
        将名称分词

        Args:
            name: 球队名称

        Returns:
            list: 词列表
    """
    # 使用正则提取所有单词(字母、数字、中文)
    tokens = re.findall(r'[\w\u4e00-\u9fff]+', name.lower())
    return tokens


def _remove_stopwords(tokens: List[str]) -> List[str]:
    """
            删除停用词

            Args:
                tokens: 词列表

            Returns:
                list: 过滤后的词列表
    """
    # 只删除完全匹配的停用词,且不在保留词列表中
    filtered = [
        token for token in tokens
        if token not in _STOPWORDS or token in _PRESERVE_WORDS
    ]
    return filtered


def _replace_synonyms(tokens: List[str]) -> List[str]:
    """
        同义词替换

        Args:
            tokens: 词列表

        Returns:
            list: 替换后的词列表
    """
    # 只替换完全匹配的词
    replaced = [_SYNONYMS.get(token, token) for token in tokens]
    return replaced


# ==================== 公开函数 ====================

def normalize_name(name: str) -> str:
    """
        标准化球队名称(推荐使用)

        完整的标准化流程:
        1. 基础清理(移除括号、特殊符号)
        2. 分词
        3. 删除停用词(fc, sc, ac等)
        4. 同义词替换(utd→united, st→saint等)
        5. 重组
        6. 执行clear_name最终清理

        Args:
            name: 原始球队名称

        Returns:
            str: 标准化后的名称

        Examples:
            >>> normalize_name("Manchester United F.C.")
            'manchesterunited'

            >>> normalize_name("Real Madrid C.F.")
            'realmadrid'

            >>> normalize_name("FC Barcelona")
            'barcelona'

            >>> normalize_name("Man Utd")
            'manunited'
    """
    if not name:
        return ''

    # 1. 基础清理
    cleaned = _basic_clean(name)

    # 2. 分词
    tokens = _tokenize(cleaned)

    # 3. 删除停用词
    tokens = _remove_stopwords(tokens)

    # 4. 同义词替换
    tokens = _replace_synonyms(tokens)

    # 5. 重组(用空格连接)
    normalized = ' '.join(tokens)

    # 6. 执行clear_name最终清理
    return clear_name(normalized)


def clear_name(name: str) -> str:
    """
    标准化联赛名称(向后兼容,保留原有逻辑)
    移除括号内容及特殊字符,并转为小写

    Args:
        name: 原始名称

    Returns:
        str: 清理后的名称(无空格)
    """
    if not name:
        return ''

    # 移除各种括号及括号内的内容
    league_name = re.sub(r'\([^)]*\)', '', name)
    league_name = re.sub(r'\[[^\]]*\]', '', league_name)
    league_name = re.sub(r'\{[^}]*\}', '', league_name)
    league_name = re.sub(r'<[^>]*>', '', league_name)

    # 使用translate一次性移除/替换所有特殊字符
    # 将.,替换为空格,其他特殊字符直接删除
    translation_table = str.maketrans({
        '"': '', "'": '', '`': '',
        '.': ' ', ',': ' ',
        '-': '', '_': '', '\\': '', '/': '',
        '&': '', '+': '', '*': '', '#': '',
        '@': '', '|': '', '~': '',
        '–': '', '—': ''
    })
    league_name = league_name.translate(translation_table)

    # 移除所有空格并转为小写
    league_name = league_name.replace(' ', '').lower().strip()

    return league_name


if __name__ == "__main__":
    # 测试用例
    test_cases = [
        "Manchester United F.C.",
        "Real Madrid C.F.",
        "FC Barcelona",
        "Man Utd",
        "St. Louis Blues",
        "Deportivo La Coruña",
        "Athletic Bilbao",
        "Internacional Porto Alegre",
        "Olympique Marseille",
        "Los Angeles Lakers BC",
        "北京国安俱乐部",
        "Primera A, Clausura"
    ]

    print("=" * 60)
    print("球队名称标准化测试")
    print("=" * 60)

    for name in test_cases:
        normalized = normalize_name(name)
        cleared = clear_name(name)
        print(f"\n原始: {name}")
        print(f"标准化: {normalized}")
        print(f"清理(旧): {cleared}")
