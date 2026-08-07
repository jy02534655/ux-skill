#!/usr/bin/env python3
"""
自动分块脚本（以章节边界优先）
用法: python split_chunks.py --input novel.txt --output_dir ./chunks --max_chars 80000
"""

import re
import argparse
from pathlib import Path

CHAPTER_PATTERN = re.compile(
    r'^\s*(?:第[零一二三四五六七八九十百千万]+[章回节]|第\d+[章回节])',
    re.MULTILINE
)


def split_by_chapters(text, max_chars=80000, overlap=500):
    """
    按章节边界分块，保持章节完整性，不丢失内容
    使用 chunk_start 记录块在原文中的绝对位置，切分点设在上一个章节开始处
    """
    chapters = list(CHAPTER_PATTERN.finditer(text))

    if not chapters:
        # 无章节，按固定大小切分
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + max_chars, len(text))
            chunks.append(text[start:end])
            start = end
        return chunks

    chunks = []
    chunk_start = 0  # 当前块在原文中的起始位置

    for i in range(1, len(chapters)):
        # 如果从 chunk_start 到当前章节开始超过 max_chars
        if chapters[i].start() - chunk_start > max_chars:
            # 在上一个章节开始处切分
            # 块包含从 chunk_start 到上一个章节开始前的所有内容
            split_pos = chapters[i-1].start()
            chunks.append(text[chunk_start:split_pos])
            # 新块从 split_pos 往前 overlap 处开始
            chunk_start = max(0, split_pos - overlap)

    # 最后一块（包含剩余所有内容）
    chunks.append(text[chunk_start:])

    return chunks


def main():
    parser = argparse.ArgumentParser(description='按章节边界分块小说文件')
    parser.add_argument('--input', required=True, help='输入小说文件路径')
    parser.add_argument('--output_dir', required=True, help='分块输出目录')
    parser.add_argument('--max_chars', type=int, default=80000, help='每块最大字符数，默认80000')
    parser.add_argument('--prefix', default='part', help='分块文件名前缀，默认part')
    parser.add_argument('--overlap', type=int, default=500, help='块间重叠字符数，默认500')
    args = parser.parse_args()

    # 读取文件
    with open(args.input, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()

    # 分块
    chunks = split_by_chapters(text, args.max_chars, args.overlap)

    # 输出
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    total_chars = 0
    for i, chunk in enumerate(chunks, 1):
        out_file = out_dir / f"{args.prefix}{i}.txt"
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(chunk)
        total_chars += len(chunk)
        print(f"分块 {i}: {len(chunk)} 字符 -> {out_file}")

    print(f"\n共 {len(chunks)} 个分块，总字符数: {total_chars}")
    print(f"原文总字符数: {len(text)}")
    print(f"重叠字符数（允许）: {total_chars - len(text)}")


if __name__ == '__main__':
    main()