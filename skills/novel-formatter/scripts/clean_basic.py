#!/usr/bin/env python3
"""
规整层处理：纯本地排版清洗和章节标题保留（基于临时目录）
用法: python clean_basic.py --batch --source ./NovelLibrary_Temp --output_dir ./NovelLibrary_Processed
      python clean_basic.py --input "NovelLibrary_Temp/分类/书名.txt" --output "NovelLibrary_Processed/分类/书名.txt"
"""

import os
import re
import json
import argparse
from pathlib import Path

# 导入公共正则和工具函数
from chapter_patterns import CHAPTER_REGEX, SPECIAL_CHAPTERS, chinese_to_number_simple


def smart_punct_convert(text):
    """标点转换保护小数点、网址、英文缩写、省略号"""
    protected = []

    def protect(m):
        protected.append(m.group(0))
        return f"\x00{len(protected)-1}\x00"

    text = re.sub(r'\d+\.\d+', protect, text)
    text = re.sub(r'[a-zA-Z]\.[a-zA-Z]', protect, text)
    text = re.sub(r'\.{3,}', protect, text)
    text = re.sub(r'https?://[^\s]+', protect, text)

    punct_map = {
        ',': '，', '!': '！', '?': '？',
        ';': '；', ':': '：',
        '(': '（', ')': '）', '[': '【', ']': '】'
    }
    for eng, chn in punct_map.items():
        text = text.replace(eng, chn)

    text = re.sub(r'(?<![a-zA-Z0-9])\.(?![a-zA-Z0-9])', '。', text)

    for i, s in enumerate(protected):
        text = text.replace(f"\x00{i}\x00", s)

    return text


def clean_text(text):
    """执行排版清洗"""
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    lines = [line.rstrip() for line in text.splitlines()]

    cleaned_lines = []
    prev_empty = False
    for line in lines:
        is_empty = (line.strip() == '')
        if is_empty and prev_empty:
            continue
        cleaned_lines.append(line)
        prev_empty = is_empty
    text = '\n'.join(cleaned_lines)

    text = re.sub(r'[ \t]+', '', text)
    text = smart_punct_convert(text)

    # 全角空格规范化
    text = text.replace('\u3000', ' ')

    return text


def replace_chapter(match):
    """将章节标题格式化为 第X章 标题 格式，保留原标题内容"""
    full = match.group(0).strip()

    if SPECIAL_CHAPTERS.match(full):
        return full

    # 匹配 第X章 标题 格式（使用公共转换函数）
    m = re.search(r'第([零一二三四五六七八九十百千万\d]+)[章回节](?:\s+(.*))?$', full)
    if m:
        num_str, title = m.group(1), m.group(2) or ''
        num = chinese_to_number_simple(num_str)
        if num is not None:
            if title:
                return f"第{num}章 {title}"
            return f"第{num}章"
        # 如果转换失败，保留原标题
        return full

    # 匹配 Chapter X 标题 格式
    m = re.search(r'Chapter\s*(\d+)(?:\s+(.*))?$', full, re.IGNORECASE)
    if m:
        num, title = m.group(1), m.group(2) or ''
        if title:
            return f"第{num}章 {title}"
        return f"第{num}章"

    # 匹配 一、标题 格式
    m = re.search(r'^([零一二三四五六七八九十百千万\d]+)[、．.]\s*(.*)$', full)
    if m:
        num_str, title = m.group(1), m.group(2) or ''
        num = chinese_to_number_simple(num_str)
        if num is not None:
            if title:
                return f"第{num}章 {title}"
            return f"第{num}章"
        return full

    return full


def normalize_chapters(text):
    """规整层章节标准化：只做格式转换，不重新编号"""
    lines = text.splitlines()
    new_lines = []
    for line in lines:
        if CHAPTER_REGEX.match(line):
            new_lines.append(replace_chapter(line))
        else:
            new_lines.append(line)
    return '\n'.join(new_lines)


def process_file(input_path, output_path):
    """处理单个文件"""
    with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    cleaned = clean_text(content)
    final = normalize_chapters(cleaned)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final)

    matches = CHAPTER_REGEX.findall(final)
    return len(matches)


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
    results = []
    success_count = 0
    failed_count = 0
    total = len(files)

    from progress_manager import update_phase
    update_phase('regular_layer', 'in_progress', total=total, processed=0, failed=0)

    for idx, item in enumerate(files):
        rel_path = item.get('relative_path', item.get('path', ''))
        if not rel_path:
            continue
        src_full = source / rel_path
        out_full = output / rel_path
        if not src_full.exists():
            print(f"跳过不存在的文件: {rel_path}")
            continue
        try:
            count = process_file(src_full, out_full)
            print(f"处理完成: {rel_path} (章节数: {count})")
            results.append({'path': rel_path, 'status': 'success', 'chapters': count})
            success_count += 1
        except Exception as e:
            print(f"处理失败: {rel_path} - {e}")
            results.append({'path': rel_path, 'status': 'error', 'error': str(e)})
            failed_count += 1

        update_phase('regular_layer', 'in_progress',
                     total=total,
                     processed=success_count + failed_count,
                     failed=failed_count,
                     current_file=rel_path)

    with open(progress_dir / 'regular_processed.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    update_phase('regular_layer', 'completed',
                 total=total,
                 processed=success_count,
                 failed=failed_count)

    print(f"规整层处理完成: 成功 {success_count}, 失败 {failed_count}")
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', help='输入文件路径（临时目录）')
    parser.add_argument('--output', help='输出文件路径（最终目录）')
    parser.add_argument('--batch', action='store_true', help='批量处理模式')
    parser.add_argument('--source', default='./NovelLibrary_Temp')
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