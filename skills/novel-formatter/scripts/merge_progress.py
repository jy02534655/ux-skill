#!/usr/bin/env python3
"""
合并分块结果，支持断点续传
用法: python merge_progress.py --merge --chunks_dir ./chunks --output ./output.txt
      python merge_progress.py --status --chunks_dir ./chunks
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path


PROGRESS_PATTERN = re.compile(r'【进度】[^\n]*')


def load_progress(progress_file):
    if not progress_file.exists():
        return {
            'book_name': '',
            'category': '',
            'processed_segments': [],
            'total_segments': 0
        }
    with open(progress_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_progress(progress_file, progress):
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def extract_segment_id(path):
    name = path.stem
    match = re.search(r'part(\d+)', name, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return 0


def parse_progress_mark(content):
    """修正 P1-3: 更健壮的进度标记解析"""
    match = PROGRESS_PATTERN.search(content)
    if match:
        mark = match.group(0)
        # 提取章节号
        chapter_match = re.search(r'已处理到第(\d+)章', mark)
        if chapter_match:
            return chapter_match.group(1), mark
        # 提取章节列表
        list_match = re.search(r'章节列表=([^\s|]+)', mark)
        if list_match:
            return list_match.group(1), mark
    return None, None


def merge_chunks(chunk_files, output_path, progress_dir=None):
    """合并分块文件"""
    sorted_files = sorted(chunk_files, key=extract_segment_id)
    
    merged = []
    chapter_list = []
    
    for chunk_file in sorted_files:
        with open(chunk_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            # 提取进度标记（修正 P1-3: 使用更健壮的解析）
            chapter_info, progress_mark = parse_progress_mark(content)
            if progress_mark:
                # 移除进度标记行
                content = content.replace(progress_mark, '')
                # 清理多余空行
                content = re.sub(r'\n{3,}', '\n\n', content)
            
            if chapter_info:
                chapter_list.append(chapter_info)
            
            merged.append(content.strip())
    
    # 写入最终文件
    final_content = '\n\n'.join(merged)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    print(f"合并完成: {output_path}")
    print(f"分块数: {len(sorted_files)}")
    if chapter_list:
        print(f"章节信息: {', '.join(chapter_list[:10])}" + 
              (f" ... 共{len(chapter_list)}个" if len(chapter_list) > 10 else ""))


def show_status(chunks_dir):
    """显示分块状态"""
    chunks_path = Path(chunks_dir)
    files = list(chunks_path.glob('*part*.txt'))
    print(f"分块目录: {chunks_dir}")
    print(f"分块文件数: {len(files)}")
    for f in sorted(files, key=extract_segment_id):
        size = f.stat().st_size
        print(f"  {f.name} ({size/1024:.1f}KB)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--merge', action='store_true', help='合并分块')
    parser.add_argument('--status', action='store_true', help='显示分块状态')
    parser.add_argument('--chunks_dir', required=True, help='分块文件目录')
    parser.add_argument('--output', help='输出文件路径')
    parser.add_argument('--progress_dir', default='./.organizer_progress', help='进度目录')
    args = parser.parse_args()
    
    chunks_path = Path(args.chunks_dir)
    if not chunks_path.exists():
        print(f"分块目录不存在: {args.chunks_dir}")
        return
    
    if args.status:
        show_status(args.chunks_dir)
    elif args.merge:
        if not args.output:
            print("请指定 --output")
            return
        chunk_files = list(chunks_path.glob('*part*.txt'))
        if not chunk_files:
            print(f"未找到分块文件")
            return
        merge_chunks(chunk_files, Path(args.output), Path(args.progress_dir))
    else:
        print("请指定 --merge 或 --status")


if __name__ == '__main__':
    main()