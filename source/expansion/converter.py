from typing import Union

from lxml.etree import HTML
from yaml import safe_load

__all__ = ["Converter"]


class Converter:
    INITIAL_STATE = "//script/text()"
    KEYS_LINK = (
        "note",
        "noteDetailMap",
        "[-1]",
        "note",
    )
    
    # 添加视频封面的路径
    KEYS_VIDEO_POSTER = (
        "note",
        "noteDetailMap",
        "[-1]",
        "note",
        "video",
        "media",
        "stream",
        "coverUrl",
    )
    
    # 添加备用视频封面路径
    KEYS_VIDEO_POSTER_ALT = (
        "note",
        "noteDetailMap",
        "[-1]",
        "note",
        "video",
        "cover",
        "url",
    )

    def run(self, content: str) -> dict:
        data = self._convert_object(self._extract_object(content))
        return self._filter_object(data)

    def _extract_object(self, html: str) -> str:
        if not html:
            return ""
        html_tree = HTML(html)
        scripts = html_tree.xpath(self.INITIAL_STATE)
        return self.get_script(scripts)

    @staticmethod
    def _convert_object(text: str) -> dict:
        return safe_load(text.lstrip("window.__INITIAL_STATE__="))

    @classmethod
    def _filter_object(cls, data: dict) -> dict:
        result = cls.deep_get(data, cls.KEYS_LINK) or {}
        if result and result.get("type") == "video":
            # 如果是视频类型，尝试多个路径获取视频封面
            video_poster = (
                cls.deep_get(data, cls.KEYS_VIDEO_POSTER) or
                cls.deep_get(data, cls.KEYS_VIDEO_POSTER_ALT)
            )
            if video_poster:
                if not video_poster.startswith(("http://", "https://")):
                    video_poster = f"https://sns-webpic-qc.xhscdn.com/{video_poster}"
                result["video_poster"] = video_poster
        return result

    @classmethod
    def deep_get(cls, data: dict, keys: list | tuple, default=None):
        if not data:
            return default
        try:
            for key in keys:
                if key.startswith("[") and key.endswith("]"):
                    data = cls.safe_get(data, int(key[1:-1]))
                else:
                    data = data[key]
            return data
        except (KeyError, IndexError, ValueError, TypeError):
            return default

    @staticmethod
    def safe_get(data: Union[dict, list, tuple, set], index: int):
        if isinstance(data, dict):
            return list(data.values())[index]
        elif isinstance(data, list | tuple | set):
            return data[index]
        raise TypeError

    @staticmethod
    def get_script(scripts: list) -> str:
        scripts.reverse()
        for script in scripts:
            if script.startswith("window.__INITIAL_STATE__"):
                return script
        return ""
