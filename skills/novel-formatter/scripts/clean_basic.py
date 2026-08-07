#!/usr/bin/env python3
"""
规整层处理：纯本地排版清洗和章节标题正则替换
用法: python clean_basic.py --input input.txt --output output.txt
"""

import os
import re
import sys
import argparse
from pathlib import Path
import json

# 章节正则（用于规整层直接替换）
CHAPTER_REGEX = re.compile(
    r'(?:第[零一二三四五六七八九十百千万]+章|第\d+章|Chapter\s*\d+|第[零一二三四五六七八九十百千万]+节|第\d+节|[\(（]?\d+[\)）]|[零一二三四五六七八九十百千万]+[、\. ]|[※☆★●◆◇○■□▲△▶►]+)',
    re.IGNORECASE
)


def clean_text(text):
    """执行排版清洗"""
    # 统一换行符
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # 删除行首行尾空格制表符
    lines = [line.strip() for line in text.splitlines()]
    
    # 删除连续空行（保留1个空行）
    cleaned_lines = []
    prev_empty = False
    for line in lines:
        is_empty = (line == '')
        if is_empty and prev_empty:
            continue
        cleaned_lines.append(line)
        prev_empty = is_empty
    text = '\n'.join(cleaned_lines)
    
    # 标点全角转换
    punct_map = {
        ',': '，', '.': '。', '!': '！', '?': '？',
        ';': '；', ':': '：', '"': '“', "'": '‘',
        '(': '（', ')': '）', '<': '〈', '>': '〉'
    }
    for eng, chn in punct_map.items():
        text = text.replace(eng, chn)
    
    # 删除多余的空格（保留一个空格分隔）
    text = re.sub(r'[ \t]+', ' ', text)
    
    return text


def replace_chapters(text):
    """使用正则替换章节标题为 '第X章' 格式"""
    # 先提取所有章节匹配，按出现顺序编号
    matches = list(CHAPTER_REGEX.finditer(text))
    if not matches:
        return text, 0
    
    # 从后往前替换避免偏移
    for idx, match in enumerate(reversed(matches), 1):
        new_title = f'第{len(matches) - idx + 1}章'
        start, end = match.start(), match.end()
        text = text[:start] + new_title + text[end:]
    
    return text, len(matches)


def process_file(input_path, output_path):
    """处理单个文件"""
    with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    cleaned = clean_text(content)
    final, count = replace_chapters(cleaned)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final)
    
    return count


def batch_process(source_dir, output_dir):
    """批量处理规整层文件"""
    source = Path(source_dir)
    output = Path(output_dir)
    progress_dir = output / '.organizer_progress'
    regular_list = progress_dir / 'regular_list.json'
    
    if not regular_list.exists():
        print("未找到规整层清单，请先运行 scan_and_classify.py")
        return
    
    with open(regular_list, 'r', encoding='utf-8') as f:
        files = json.load(f)
    
    print(f"开始处理规整层 {len(files)} 个文件...")
    for item in files:
        rel_path = item['path']
        src_full = source / rel_path
        out_full = output / rel_path
        if not src_full.exists():
            print(f"跳过不存在的文件: {rel_path}")
            continue
        try:
            count = process_file(src_full, out_full)
            print(f"处理完成: {rel_path} (章节数: {count})")
        except Exception as e:
            print(f"处理失败: {rel_path} - {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', help='输入文件路径')
    parser.add_argument('--output', help='输出文件路径')
    parser.add_argument('--batch', action='store_true', help='批量处理模式')
    parser.add_argument('--source', default='./NovelLibrary')
    parser.add_argument('--output_dir', default='./NovelLibrary_Processed')
    args = parser.parse_args()
    
    if args.batch:
        batch_process(args.source, args.output_dir)
    elif args.input and args.output:
        process_file(Path(args.input), Path(args.output))
    else:
        print("请指定 --input 和 --output 或 --batch")


if __name__ == '__main__':
    main()