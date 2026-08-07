#!/usr/bin/env python3
"""
合并分块结果，支持断点续传
用法: python merge_progress.py --book 射雕英雄传 --chunks ./chunks --output ./output
"""

import os
import sys
import json
import re
import argparse
from pathlib import Path
from datetime import datetime


def load_progress(progress_file):
    """读取进度文件"""
    if not progress_file.exists():
        return {
            'book_name': '',
            'category': '',
            'last_chapter': 0,
            'processed_segments': [],
            'total_segments': 0
        }
    with open(progress_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_progress(progress_file, progress):
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def merge_chunks(chunk_files, output_path, progress_file=None):
    """合并分块文件"""
    progress = load_progress(progress_file) if progress_file else None
    
    # 按片段序号排序
    def extract_segment_id(path):
        # 从文件名提取序号，如 book_part1.txt -> 1
        name = path.stem
        match = re.search(r'part(\d+)', name, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return 0
    
    sorted_files = sorted(chunk_files, key=extract_segment_id)
    
    # 如果存在进度，只合并未处理的部分
    if progress:
        processed = set(progress.get('processed_segments', []))
        sorted_files = [f for f in sorted_files if extract_segment_id(f) not in processed]
    
    # 合并
    merged = []
    chapter_count = progress.get('last_chapter', 0) if progress else 0
    
    for chunk_file in sorted_files:
        with open(chunk_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            # 提取进度标记行（以【进度】开头）
            lines = content.splitlines()
            if lines and lines[-1].startswith('【进度】'):
                # 移除进度标记行
                content = '\n'.join(lines[:-1])
                # 解析进度
                match = re.search(r'已处理到第(\d+)章', lines[-1])
                if match:
                    chapter_count = int(match.group(1))
            merged.append(content)
            
            if progress_file:
                # 更新进度
                seg_id = extract_segment_id(chunk_file)
                if seg_id not in progress.get('processed_segments', []):
                    progress['processed_segments'].append(seg_id)
                    progress['last_chapter'] = chapter_count
                    save_progress(progress_file, progress)
    
    # 写入最终文件
    final_content = '\n\n'.join(merged)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    print(f"合并完成: {output_path}")
    print(f"总章节数: {chapter_count}")


def extract_chapters(text):
    """从已合并文本中提取章节映射"""
    pattern = re.compile(r'^第\d+章', re.MULTILINE)
    matches = pattern.findall(text)
    chapters = []
    for m in matches:
        num = re.search(r'\d+', m)
        if num:
            chapters.append(int(num.group()))
    return chapters


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--book', required=True, help='书名')
    parser.add_argument('--category', required=True, help='分类名')
    parser.add_argument('--chunks_dir', required=True, help='分块文件目录')
    parser.add_argument('--output', required=True, help='输出文件路径')
    parser.add_argument('--progress_dir', default='./.organizer_progress', help='进度目录')
    args = parser.parse_args()
    
    # 查找分块文件
    chunks_path = Path(args.chunks_dir)
    chunk_files = list(chunks_path.glob(f'{args.book}_part*.txt'))
    
    if not chunk_files:
        print(f"未找到 {args.book} 的分块文件")
        return
    
    # 进度文件
    progress_file = Path(args.progress_dir) / f'{args.book}.progress'
    
    merge_chunks(chunk_files, Path(args.output), progress_file)


if __name__ == '__main__':
    main()