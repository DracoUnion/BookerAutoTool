import json
import os
from os import path
import re
from typing import Any, Optional, Type

import yaml
from pydantic import BaseModel, parse_obj_as, ValidationError


def d(name):
    DIR = path.dirname(path.abspath(__file__))
    return path.join(DIR, name)


def render_prompt(prompt: str, **kw):
    return re.sub(r"{(\w+)}", lambda g: kw.get(g.group(1), g.group(0)), prompt)


def read_text(fname: str) -> str:
    """以 UTF-8 读取 fname 的文本内容。"""
    if not path.isfile(fname):
        return None
    text = open(fname, encoding='utf8').read()
    chs = set(text)
    # 避免读取损坏的数据
    if len(chs) == 1 and '\x00' in chs:
        text = ""
    return text


def write_text(fname: str, text: str, append: bool = False) -> None:
    """将 text 以 UTF-8 写入 fname（自动创建父目录）。"""
    os.makedirs(path.dirname(fname), exist_ok=True)
    open(fname, 'a' if append else 'w', encoding='utf8').write(text)


def json_dump_model(obj) -> str:
    """将对象（含 pydantic 模型/列表）序列化为 JSON 字符串。"""
    if isinstance(obj, BaseModel):
        obj = obj.model_dump()
    elif isinstance(obj, list):
        obj = [
            it.dict() if isinstance(it, BaseModel) else it
            for it in obj
        ]
    return json.dumps(obj, ensure_ascii=False)


def read_yaml_model(fname: str, model: Optional[Type[BaseModel]]):
    """从 fname 读取 YAML 并解析为指定 pydantic 模型；文件缺失或损坏时返回 None。"""
    if not path.isfile(fname) or not path.getsize(fname):
        return None
    try:
        data = yaml.safe_load(open(fname, encoding='utf8').read())
        return parse_obj_as(model, data) if model else data
    except yaml.error.YAMLError:
        return None
    except ValidationError:
        return None


def write_yaml_model(fname: str, obj: Any) -> None:
    """将对象（含 pydantic 模型/列表）以 YAML 形式写入 fname。"""
    if isinstance(obj, BaseModel):
        obj = obj.dict()
    elif isinstance(obj, list):
        obj = [
            it.dict() if isinstance(it, BaseModel) else it
            for it in obj
        ]
    os.makedirs(path.dirname(fname), exist_ok=True)
    with open(fname, 'w', encoding='utf8') as f:
        yaml.safe_dump(obj, f, allow_unicode=True, sort_keys=False)


ext_code_block = lambda s: re.search(r'```\w*([\s\S]+)```', s).group(1)