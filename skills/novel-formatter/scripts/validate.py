#!/usr/bin/env python3
"""
校验最终输出
用法: python validate.py
"""

import os
import sys
import json
import re
import argparse
from pathlib import Path
from datetime import datetime


def count_chapters(text):
    """统计章节数并检查连续性"""
    # 匹配 "第X章" 格式
    pattern = re.compile(r'^第\d+章', re.MULTILINE)
    matches = pattern.findall(text)
    
    if not matches:
        return 0, [], True
    
    # 提取章节号
    numbers = []
    for m in matches:
        num = re.search(r'\d+', m)
        if num:
            numbers.append(int(num.group()))
    
    if not numbers:
        return 0, [], True
    
    # 检查是否从1开始连续
    is_continuous = True
    expected = 1
    for n in numbers:
        if n != expected:
            is_continuous = False
            break
        expected += 1
    
    return len(numbers), numbers, is_continuous


def validate_file(file_path):
    """校验单个文件"""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    total_chars = len(content)
    lines = content.splitlines()
    non_empty_lines = len([l for l in lines if l.strip()])
    
    chapter_count, chapter_numbers, is_continuous = count_chapters(content)
    
    # 检查标题格式是否统一（所有标题必须为"第X章"）
    title_pattern = re.compile(r'^第\d+章$', re.MULTILINE)
    # 检查是否有其他格式的标题残留
    other_pattern = re.compile(
        r'^(?:第[零一二三四五六七八九十百千万]+[章回节]|Chapter\s*\d+|[\(（]?\d+[\)）]|[零一二三四五六七八九十百千万]+[、\.]|[※☆★●◆◇○■□▲△▶►]+)',
        re.MULTILINE
    )
    # 排除已经规范化的"第X章"
    other_matches = [m for m in other_pattern.finditer(content) 
                     if not re.match(r'^第\d+章$', m.group())]
    
    issues = []
    if not is_continuous:
        issues.append(f"章节编号不连续: {chapter_numbers[:10]}...")
    if other_matches:
        issues.append(f"发现 {len(other_matches)} 个未规范化的标题残留")
    
    return {
        'file_path': str(file_path),
        'total_chars': total_chars,
        'non_empty_lines': non_empty_lines,
        'chapter_count': chapter_count,
        'is_continuous': is_continuous,
        'has_other_titles': len(other_matches) > 0,
        'other_title_count': len(other_matches),
        'issues': issues,
        'passed': len(issues) == 0
    }


def validate_all(output_dir):
    """校验所有输出文件"""
    output_path = Path(output_dir)
    progress_dir = output_path / '.organizer_progress'
    
    # 读取分类报告，获取所有待处理文件
    classification_file = progress_dir / 'classification.json'
    if not classification_file.exists():
        print("未找到分类报告，请先运行 scan_and_classify.py")
        return
    
    with open(classification_file, 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    results = []
    for detail in report.get('details', []):
        if detail.get('layer') == 'error':
            continue
        rel_path = detail.get('relative_path')
        if not rel_path:
            continue
        out_file = output_path / rel_path
        if not out_file.exists():
            results.append({
                'file_path': rel_path,
                'passed': False,
                'issues': ['输出文件不存在']
            })
            continue
        result = validate_file(out_file)
        results.append(result)
    
    # 统计
    passed = sum(1 for r in results if r.get('passed', False))
    total = len(results)
    
    # 生成报告
    report_file = progress_dir / 'validation_report.json'
    validation_result = {
        'validate_time': datetime.now().isoformat(),
        'total': total,
        'passed': passed,
        'failed': total - passed,
        'details': results
    }
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(validation_result, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*50)
    print("校验完成")
    print(f"总计: {total} 个文件")
    print(f"通过: {passed}")
    print(f"失败: {total - passed}")
    print(f"报告已保存: {report_file}")
    print("="*50)
    
    # 打印失败列表
    failed_items = [r for r in results if not r.get('passed', False)]
    if failed_items:
        print("\n失败文件列表:")
        for item in failed_items:
            issues = item.get('issues', ['未知错误'])
            print(f"  - {item.get('file_path', 'unknown')}: {', '.join(issues)}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='./NovelLibrary_Processed')
    args = parser.parse_args()
    
    validate_all(args.output)


if __name__ == '__main__':
    main()