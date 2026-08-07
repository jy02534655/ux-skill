#!/usr/bin/env python3
"""
半规整层：提取候选章节行，根据映射表执行全文替换
用法: python chapter_replace.py --input input.txt --output output.txt --mapping mapping.json
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path

# 候选章节提取正则（宽松）
CANDIDATE_REGEX = re.compile(
    r'^.{0,20}(?:第[零一二三四五六七八九十百千万]+[章回节]|第\d+[章回节]|Chapter\s*\d+|[\(（]?\d+[\)）]|[零一二三四五六七八九十百千万]+[、\.]|[※☆★●◆◇○■□▲△▶►]+).{0,30}$',
    re.MULTILINE | re.IGNORECASE
)


def extract_candidates(text):
    """提取疑似章节标题行"""
    lines = text.splitlines()
    candidates = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if len(stripped) < 2:
            continue
        if CANDIDATE_REGEX.search(line):
            candidates.append({
                'index': i,
                'line': stripped,
                'context': lines[max(0, i-1):min(len(lines), i+2)]
            })
    return candidates


def apply_mapping(text, mapping):
    """根据映射表替换章节标题"""
    # mapping: [{"original": "...", "new": "第X章"}, ...]
    # 从后往前替换避免偏移
    for item in reversed(mapping):
        orig = item['original'].strip()
        new = item['new']
        # 用正则替换，只替换独立行
        pattern = re.compile(r'^' + re.escape(orig) + r'$', re.MULTILINE)
        text = pattern.sub(new, text)
    return text


def process_file(input_path, output_path, mapping_path):
    with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    with open(mapping_path, 'r', encoding='utf-8') as f:
        mapping_data = json.load(f)
    
    # 提取映射表
    mapping = mapping_data.get('mapping', [])
    if not mapping:
        print("映射表为空，直接复制原文件")
        final = content
    else:
        final = apply_mapping(content, mapping)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final)
    
    print(f"处理完成，共替换 {len(mapping)} 个章节")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='输入文件路径')
    parser.add_argument('--output', required=True, help='输出文件路径')
    parser.add_argument('--mapping', required=True, help='映射表JSON文件路径')
    args = parser.parse_args()
    
    process_file(Path(args.input), Path(args.output), Path(args.mapping))


if __name__ == '__main__':
    main()