from __future__ import annotations

import base64
import hashlib
import json
import random
import re
import uuid
from datetime import date, datetime
from urllib.parse import quote, unquote


class ToolsError(ValueError):
    pass


def format_json(text: str) -> str:
    try:
        return json.dumps(json.loads(text), ensure_ascii=False, indent=2)
    except json.JSONDecodeError as exc:
        raise ToolsError(f"JSON 无效：{exc.msg}") from exc


def minify_json(text: str) -> str:
    try:
        return json.dumps(json.loads(text), ensure_ascii=False, separators=(",", ":"))
    except json.JSONDecodeError as exc:
        raise ToolsError(f"JSON 无效：{exc.msg}") from exc


def encode_url(text: str) -> str:
    return quote(text, safe="")


def decode_url(text: str) -> str:
    return unquote(text)


def encode_base64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def decode_base64(text: str) -> str:
    raw = "".join(text.split())
    padded = raw + "=" * ((4 - len(raw) % 4) % 4)
    try:
        return base64.b64decode(padded).decode("utf-8")
    except Exception as exc:  # noqa: BLE001
        raise ToolsError("Base64 无效") from exc


def hash_md5(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def hash_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def new_uuid() -> str:
    return str(uuid.uuid4())


def parse_time_value(text: str, now: datetime | None = None) -> datetime:
    raw = (text or "").strip()
    if not raw or raw in {"现在", "now"}:
        return now or datetime.now()
    if raw.isdigit():
        value = int(raw)
        if len(raw) >= 13:
            return datetime.fromtimestamp(value / 1000)
        if len(raw) == 10:
            return datetime.fromtimestamp(value)
        raise ToolsError("时间戳需要 10 位秒或 13 位毫秒")
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    raise ToolsError("无法识别时间，试试 2026-09-11 10:32:00 或时间戳")


def time_snapshot(dt: datetime) -> dict[str, str]:
    seconds = int(dt.timestamp())
    millis = int(dt.timestamp() * 1000)
    return {
        "local": dt.strftime("%Y-%m-%d %H:%M:%S"),
        "seconds": str(seconds),
        "millis": str(millis),
    }


_STEMS = "甲乙丙丁戊己庚辛壬癸"
_BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
_WEEKDAY_INDEX = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
_DIRECTIONS = ["正北", "东北", "正东", "东南", "正南", "西南", "正西", "西北"]
_CLASH = {
    "子": "午",
    "丑": "未",
    "寅": "申",
    "卯": "酉",
    "辰": "戌",
    "巳": "亥",
    "午": "子",
    "未": "丑",
    "申": "寅",
    "酉": "卯",
    "戌": "辰",
    "亥": "巳",
}
_GOOD = [
    "写代码",
    "修缺陷",
    "提交代码",
    "写注释",
    "补测试",
    "做备份",
    "整理待办",
    "写周报",
    "读书学习",
    "早睡",
    "喝水",
    "散步",
    "会友",
    "祈福",
    "纳财",
]
_BAD = [
    "上线",
    "强制推送",
    "改生产配置",
    "删数据",
    "通宵",
    "口头承诺工期",
    "同时开一堆需求",
    "跳过测试",
    "动土装修",
    "争执",
    "借贷",
]
_TIPS = [
    "面向财神位坐下，思路会顺一些。",
    "今天适合把难讲的需求写成文档。",
    "少开会，多提交。",
    "先备份，再动手。",
    "简单的小事今天也能做成。",
]


def split_identifier(text: str) -> list[str]:
    raw = (text or "").strip()
    if not raw:
        raise ToolsError("请输入中文含义或英文变量名")
    if re.search(r"[\u4e00-\u9fff]", raw):
        raise ToolsError("中文请点「AI 起名」")
    spaced = re.sub(r"[^\w]+", " ", raw)
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", spaced)
    spaced = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", spaced)
    parts = [part.lower() for part in spaced.split() if part]
    if not parts:
        raise ToolsError("没有识别到英文单词")
    return parts


def naming_styles(parts: list[str]) -> dict[str, str]:
    words = [re.sub(r"[^a-z0-9]", "", part.lower()) for part in parts]
    words = [word for word in words if word]
    if not words:
        raise ToolsError("没有可用的英文单词")
    return {
        "snake_case": "_".join(words),
        "camelCase": words[0] + "".join(word.title() for word in words[1:]),
        "PascalCase": "".join(word.title() for word in words),
        "CONSTANT": "_".join(word.upper() for word in words),
        "kebab-case": "-".join(words),
    }


def format_naming(styles: dict[str, str]) -> str:
    return "\n".join(f"{key}: {value}" for key, value in styles.items())


def parse_name_words(text: str) -> list[str]:
    parts = [part.lower() for part in re.findall(r"[a-zA-Z]+", text)]
    if not parts:
        raise ToolsError("模型没有返回英文单词")
    return parts[:4]


def day_ganzhi(day: date) -> tuple[str, str]:
    delta = (day - date(1899, 12, 22)).days
    return _STEMS[delta % 10], _BRANCHES[delta % 12]


def almanac_for(day: date | None = None) -> str:
    day = day or date.today()
    gan, zhi = day_ganzhi(day)
    rng = random.Random(int(hashlib.md5(day.isoformat().encode("utf-8")).hexdigest(), 16))
    good = rng.sample(_GOOD, 3)
    bad_pool = [item for item in _BAD if item not in good]
    bad = rng.sample(bad_pool, 3)
    luck = _DIRECTIONS[rng.randrange(len(_DIRECTIONS))]
    wealth = _DIRECTIONS[rng.randrange(len(_DIRECTIONS))]
    tip = _TIPS[rng.randrange(len(_TIPS))]
    weekday = _WEEKDAY_INDEX[day.weekday()]
    return (
        f"{day.strftime('%Y年%m月%d日')}  {weekday}\n"
        f"{gan}{zhi}日　冲{_CLASH[zhi]}\n\n"
        f"宜  {'、'.join(good)}\n"
        f"忌  {'、'.join(bad)}\n\n"
        f"喜神 {luck}　财神 {wealth}\n"
        f"{tip}"
    )
