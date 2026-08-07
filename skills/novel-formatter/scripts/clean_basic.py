#!/usr/bin/env python3
"""
规整层处理：纯本地排版清洗和章节标题保留
用法: python clean_basic.py --batch
      python clean_basic.py --input input.txt --output output.txt
"""

import os
import re
import json
import argparse
from pathlib import Path

# 修正 P0-1: 增加 ^ 和 $ 锚定，只匹配独立行
CHAPTER_REGEX = re.compile(
    r'^\s*(?:'
    r'第[零一二三四五六七八九十百千万]+[章回节]|'
    r'第\d+[章回节]|'
    r'Chapter\s*\d+|CHAPTER\s*\d+|'
    r'[零一二三四五六七八九十百千万]+[、．.]\s*\S+|'
    r'[※☆★●◆◇○■□▲△▶►]+\s*\S+'
    r')\s*$',
    re.MULTILINE | re.IGNORECASE
)

# 特殊章节（不参与编号，但需要保留格式）
SPECIAL_CHAPTERS = re.compile(
    r'^\s*(?:序章|楔子|尾声|后记|番外|外传|引子|前言|引言|跋)',
    re.MULTILINE | re.IGNORECASE
)


def smart_punct_convert(text):
    """修正 P0-2: 标点转换保护小数点、网址、英文缩写、省略号"""
    protected = []
    
    def protect(m):
        protected.append(m.group(0))
        return f"\x00{len(protected)-1}\x00"
    
    # 保护模式
    text = re.sub(r'\d+\.\d+', protect, text)           # 小数
    text = re.sub(r'[a-zA-Z]\.[a-zA-Z]', protect, text)  # 英文缩写
    text = re.sub(r'\.{3,}', protect, text)              # 省略号
    text = re.sub(r'https?://[^\s]+', protect, text)     # URL
    
    # 安全转换
    punct_map = {
        ',': '，', '!': '！', '?': '？',
        ';': '；', ':': '：',
        '(': '（', ')': '）', '[': '【', ']': '】'
    }
    for eng, chn in punct_map.items():
        text = text.replace(eng, chn)
    
    # 句号转换：只转换不在数字/字母后的点
    text = re.sub(r'(?<![a-zA-Z0-9])\.(?![a-zA-Z0-9])', '。', text)
    
    # 恢复保护内容
    for i, s in enumerate(protected):
        text = text.replace(f"\x00{i}\x00", s)
    
    return text


def clean_text(text):
    """执行排版清洗"""
    # 统一换行符
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # 删除行首行尾空格制表符
    lines = [line.rstrip() for line in text.splitlines()]
    
    # 删除连续空行（保留1个空行）
    cleaned_lines = []
    prev_empty = False
    for line in lines:
        is_empty = (line.strip() == '')
        if is_empty and prev_empty:
            continue
        cleaned_lines.append(line)
        prev_empty = is_empty
    text = '\n'.join(cleaned_lines)
    
    # 修正 P1-2: 删除行内所有制表符和多余空格（中文小说不需要英文单词间空格）
    text = re.sub(r'[ \t]+', '', text)
    
    # 智能标点转换
    text = smart_punct_convert(text)
    
    return text


def normalize_chapters(text):
    """
    规整层章节标准化：只做格式转换，不重新编号
    例："第一章" -> "第1章"，"CHAPTER 5" -> "第5章"
    """
    # 中文数字转阿拉伯数字（简化版，只处理常见情况）
    chinese_num_map = {
        '一': '1', '二': '2', '三': '3', '四': '4', '五': '5',
        '六': '6', '七': '7', '八': '8', '九': '9', '十': '10',
        '十一': '11', '十二': '12', '十三': '13', '十四': '14', '十五': '15',
        '十六': '16', '十七': '17', '十八': '18', '十九': '19', '二十': '20'
    }
    
    def replace_chapter(match):
        full = match.group(0)
        # 提取章节号
        num_match = re.search(r'第([零一二三四五六七八九十百千万]+)章', full)
        if num_match:
            chn = num_match.group(1)
            if chn in chinese_num_map:
                new_num = chinese_num_map[chn]
            else:
                # 简单处理百千万
                new_num = chn
            return f"第{new_num}章"
        
        num_match = re.search(r'Chapter\s*(\d+)', full, re.IGNORECASE)
        if num_match:
            return f"第{num_match.group(1)}章"
        
        return full
    
    # 只转换独立行
    lines = text.splitlines()
    new_lines = []
    for line in lines:
        if CHAPTER_REGEX.match(line):
            # 检查是否为特殊章节
            if SPECIAL_CHAPTERS.match(line):
                new_lines.append(line)
            else:
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
    
    # 统计章节数
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
    for item in files:
        rel_path = item.get('path', '')
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
        except Exception as e:
            print(f"处理失败: {rel_path} - {e}")
            results.append({'path': rel_path, 'status': 'error', 'error': str(e)})
    
    # 保存处理日志
    with open(progress_dir / 'regular_processed.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    return results


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