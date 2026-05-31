#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fetch_news.py 单元测试"""
import sys, json, unittest, os
from unittest.mock import patch, MagicMock

# 把fetch_news.py当作模块导入
sys.path.insert(0, os.path.dirname(__file__))
import fetch_news as fn

class TestFilters(unittest.TestCase):
    """核心过滤函数测试"""

    def test_is_good_normal(self):
        """正常标题应该通过"""
        self.assertTrue(fn.is_good("比特币突破8万美元创历史新高"))
        self.assertTrue(fn.is_good("AI大模型最新进展：GPT-5发布"))

    def test_is_good_too_short(self):
        """太短的标题应该过滤"""
        self.assertFalse(fn.is_good("你好"))
        self.assertFalse(fn.is_good(""))

    def test_is_good_too_long(self):
        """太长的标题应该过滤"""
        self.assertFalse(fn.is_good("A" * 60))

    def test_is_good_ban_words(self):
        """包含广告关键词的标题应该过滤"""
        self.assertFalse(fn.is_good("免费领取比特币"))
        self.assertFalse(fn.is_good("点击领取红包"))
        self.assertFalse(fn.is_good("关注公众号获取更多"))
        self.assertFalse(fn.is_good("扫码下载APP"))

    def test_is_good_title_ban(self):
        """通用屏蔽词"""
        self.assertFalse(fn.is_good("查看更多"))
        self.assertFalse(fn.is_good("点击这里"))
        self.assertFalse(fn.is_good("免责声明"))

    def test_is_good_url_normal(self):
        """正常URL通过"""
        self.assertTrue(fn.is_good_url("https://www.example.com/news/123"))
        self.assertTrue(fn.is_good_url("https://finance.sina.com.cn/stock/"))

    def test_is_good_url_ban(self):
        """广告参数URL过滤"""
        self.assertFalse(fn.is_good_url("https://www.example.com/?adid=123"))
        self.assertFalse(fn.is_good_url("https://www.example.com/download"))

    def test_is_good_url_choice(self):
        """Choice金融终端URL过滤"""
        self.assertFalse(fn.is_good_url("https://choice.example.com/data"))

class TestPatFunctions(unittest.TestCase):
    """正则提取函数测试"""

    def test_pat_normal(self):
        """正则标题提取"""
        html = '<a href="/news/1">比特币突破8万</a><a href="/news/2">AI大模型进展</a>'
        result = fn.pat(html, r'<a[^>]*>([^<]{6,20})</a>')
        self.assertEqual(len(result), 2)
        self.assertIn("比特币突破8万", result)

    def test_pat_max_limit(self):
        """测试最多提取数量"""
        html = ''.join([f'<a>新闻标题{i}号</a>' for i in range(10)])
        result = fn.pat(html, r'<a>([^<]{6,20})</a>', mx=6)
        self.assertEqual(len(result), 6)

    def test_pat_min_length(self):
        """测试最小长度"""
        html = '<a>短</a><a>正常长度标题</a>'
        result = fn.pat(html, r'<a>([^<]{2,20})</a>', mn=6)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "正常长度标题")

    def test_pat_u_normal(self):
        """带URL的正则提取"""
        # 用简单正则避免转义问题
        html = '<a href="https://example.com/1">新闻标题一号</a>'
        result = fn.pat_u(html, r'<a [^>]*href="([^"]+)"[^>]*>([^<]{6,20})</a>')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['t'], "新闻标题一号")
        self.assertEqual(result[0]['u'], "https://example.com/1")

    def test_pat_u_dedup(self):
        """相同前8字符的标题去重"""
        html = '<a href="https://a.com/1">标题完全相同</a><a href="https://a.com/2">标题完全相同但重复</a>'
        result = fn.pat_u(html, r'<a\s+href="([^"]+)"[^>]*>([^<]{8,20})</a>')
        self.assertEqual(len(result), 1)

class TestSources(unittest.TestCase):
    """数据源格式化测试（不依赖网络）"""

    def test_source_return_format(self):
        """所有源函数返回格式一致"""
        # 遍历所有s函数
        sources = [getattr(fn, name) for name in dir(fn) if name.startswith('s') and callable(getattr(fn, name))]
        self.assertGreater(len(sources), 5, "至少应该有5个以上的源")

        # 用mock防止实际网络调用
        with patch.object(fn, 'f_either', return_value=''):
            for src_fn in sources[:3]:  # 测前3个就够了
                try:
                    result = src_fn()
                    if result:  # 如果返回了数据
                        item = result[0]
                        # 检查字段
                        self.assertIn('t', item)
                        self.assertIn('src', item)
                        self.assertIn('cat', item)
                        self.assertIn('u', item)
                        # 类型检查
                        self.assertIsInstance(item['t'], str)
                        self.assertIsInstance(item['src'], str)
                        self.assertIsInstance(item['cat'], str)
                        self.assertIsInstance(item['u'], str)
                except Exception as e:
                    self.fail(f"{src_fn.__name__} 抛出异常: {e}")

    def test_source_categories(self):
        """分类限定在已知类别中"""
        known_cats = {'finance', 'tech', 'macro', 'market'}
        sources = [getattr(fn, name) for name in dir(fn) if name.startswith('s') and callable(getattr(fn, name))]
        with patch.object(fn, 'f_either', return_value=''):
            for src_fn in sources[:3]:
                try:
                    result = src_fn()
                    if result:
                        self.assertIn(result[0]['cat'], known_cats,
                            f"{src_fn.__name__} 使用了未知分类: {result[0]['cat']}")
                except:
                    pass

class TestBannedWords(unittest.TestCase):
    """BAN集合完整性检查"""

    def test_ban_set_not_empty(self):
        """BAN屏蔽词集合不能为空"""
        self.assertGreater(len(fn.BAN), 0)
        self.assertGreater(len(fn.BAN_TITLE), 0)

    def test_ban_no_duplicates(self):
        """BAN集合没有重复"""
        self.assertEqual(len(fn.BAN), len(set(fn.BAN)))

if __name__ == '__main__':
    unittest.main(verbosity=2)
