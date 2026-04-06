"""共享缓存键与失效辅助（板块树、与 Django Cache 一致）。"""
from django.core.cache import cache

# 与 BoardListView 默认根查询一致；变更时请同步迁移旧键或接受短期未命中
BOARD_TREE_ROOT_CACHE_KEY = 'boards:tree:root:v1'


def invalidate_board_tree_cache() -> None:
    cache.delete(BOARD_TREE_ROOT_CACHE_KEY)
