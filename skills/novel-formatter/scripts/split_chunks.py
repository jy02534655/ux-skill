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
    """按章节边界分块，保持章节完整性"""
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
    
    # 按章节边界分块
    chunks = []
    current_start = 0
    current_text = ""
    
    for i, match in enumerate(chapters):
        chapter_start = match.start()
        # 如果当前块已满且非空，保存并开始新块
        if len(current_text) + (chapter_start - current_start) > max_chars and current_text:
            chunks.append(current_text)
            # 新块保留上一块末尾 overlap 字符作为上下文
            overlap_start = max(0, chapter_start - overlap)
            current_text = text[overlap_start:chapter_start]
            current_start = chapter_start
        
        current_text += text[current_start:chapter_start]
        current_start = chapter_start
    
    # 最后一块
    if current_start < len(text):
        current_text += text[current_start:]
    if current_text:
        chunks.append(current_text)
    
    return chunks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='输入小说文件')
    parser.add_argument('--output_dir', required=True, help='分块输出目录')
    parser.add_argument('--max_chars', type=int, default=80000, help='每块最大字符数')
    parser.add_argument('--prefix', default='part', help='分块文件名前缀')
    parser.add_argument('--overlap', type=int, default=500, help='块间重叠字符数')
    args = parser.parse_args()
    
    with open(args.input, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()
    
    chunks = split_by_chapters(text, args.max_chars, args.overlap)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    for i, chunk in enumerate(chunks, 1):
        out_file = out_dir / f"{args.prefix}{i}.txt"
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(chunk)
        print(f"分块 {i}: {len(chunk)} 字符 -> {out_file}")
    
    print(f"共 {len(chunks)} 个分块")


if __name__ == '__main__':
    main()