"""Tag normalization: map platform-specific tags to unified categories."""

# Mapping from raw platform tags to unified categories
TAG_MAP = {
    # DP / Dynamic Programming
    'dp': 'DP',
    'dynamic programming': 'DP',
    'dynamic programing': 'DP',
    '动态规划': 'DP',

    # Graph
    'graphs': 'Graph',
    'graph': 'Graph',
    'graph theory': 'Graph',
    'dfs and similar': 'Graph',
    'dfs': 'Graph',
    'bfs': 'Graph',
    'shortest paths': 'Graph',
    'trees': 'Graph',
    'tree': 'Graph',
    '图论': 'Graph',
    '生成树': 'Graph',
    '拓扑排序': 'Graph',
    'lca': 'Graph',

    # Greedy
    'greedy': 'Greedy',
    'greedy algorithms': 'Greedy',
    '贪心': 'Greedy',

    # Math
    'math': 'Math',
    'mathematics': 'Math',
    'number theory': 'Math',
    'combinatorics': 'Math',
    'probability': 'Math',
    'matrices': 'Math',
    'fft': 'Math',
    '数学': 'Math',
    '数论': 'Math',
    '概率': 'Math',
    '组合数学': 'Math',
    '计数': 'Math',

    # Data Structure
    'data structures': 'DataStructure',
    'data structure': 'DataStructure',
    'ds': 'DataStructure',
    'segment tree': 'DataStructure',
    'fenwick tree': 'DataStructure',
    'binary indexed tree': 'DataStructure',
    'bitmask': 'DataStructure',
    'hashes': 'DataStructure',
    '数据结构': 'DataStructure',
    '线段树': 'DataStructure',
    '并查集': 'DataStructure',
    '堆': 'DataStructure',
    '单调队列': 'DataStructure',

    # Implementation
    'implementation': 'Implementation',
    'constructive algorithms': 'Implementation',
    'brute force': 'Implementation',
    '模拟': 'Implementation',
    '高精度': 'Implementation',

    # String
    'strings': 'String',
    'string': 'String',
    '字符串': 'String',
    'trie': 'String',
    '后缀数组': 'String',

    # Geometry
    'geometry': 'Geometry',
    'computational geometry': 'Geometry',
    '几何': 'Geometry',

    # Search
    'binary search': 'Search',
    'ternary search': 'Search',
    'meet-in-the-middle': 'Search',
    '二分': 'Search',
    '搜索': 'Search',
    '搜索/回溯': 'Search',

    # Other common tags
    'two pointers': 'Implementation',
    'sortings': 'Implementation',
    'sorting': 'Implementation',
    'divide and conquer': 'Search',
    'recursion': 'Implementation',
    'games': 'Other',
    'flows': 'Graph',
    '2-sat': 'Graph',
    'graph matchings': 'Graph',
    'schedules': 'Other',
    'interactive': 'Other',
    'chinese remainder theorem': 'Math',
    'expression parsing': 'String',
}

UNIFIED_CATEGORIES = [
    'DP', 'Graph', 'Greedy', 'Math', 'DataStructure',
    'Implementation', 'String', 'Geometry', 'Search', 'Other',
]


def normalize_tags(raw_tags: dict) -> dict:
    """Convert platform-specific tag counts to unified categories.

    Args:
        raw_tags: Dict of {tag_name: count}

    Returns:
        Dict of {unified_category: total_count}
    """
    result = {}
    for tag, count in raw_tags.items():
        normalized = TAG_MAP.get(tag.lower().strip(), 'Other')
        result[normalized] = result.get(normalized, 0) + int(count)
    return result
