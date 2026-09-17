#!/usr/bin/env python3
"""
进度报告：快速查看整理任务的各阶段状态、失败文件与下一步建议
用法: python progress_report.py [--status]
（在包含 .organizer_progress/ 的目录下运行）
"""

import argparse
import json
from pathlib import Path

from progress_manager import get_progress, get_next_phase


def fmt_pct(done, total):
    """计算百分比，total 为 0 时显示占位符"""
    if not total:
        return '-'
    return f'{done / total * 100:.0f}%'


def main():
    parser = argparse.ArgumentParser(description='查看整理任务进度')
    parser.add_argument('--status', action='store_true', help='快速查看当前进度（等效于默认行为）')
    args = parser.parse_args()

    progress = get_progress()
    if not progress:
        print('未找到进度文件 .organizer_progress/task_progress.json')
        print('原因: 任务尚未开始，或进度目录被删除/移动')
        print('建议: 先运行 Step 0 转码（preprocess_encoding.py）；想重新开始可用 progress_manager.py --reset')
        return

    status = progress.get('status', 'unknown')
    print('=' * 55)
    print(f"任务: {progress.get('task_id', '?')}  状态: {status}")
    print(f"开始: {progress.get('start_time', '?')}  最近更新: {progress.get('last_update', '?')}")
    print('-' * 55)
    print('各阶段进度:')
    done_total = 0
    active_phase = None
    for name, phase in progress.get('phases', {}).items():
        phase_status = phase.get('status', 'pending')
        total = phase.get('total', phase.get('total_files', 0))
        processed = phase.get('processed', phase.get('processed_files', 0))
        failed = phase.get('failed', 0)
        flag = {'completed': '✔', 'in_progress': '▶', 'pending': '○', 'failed': '✖'}.get(phase_status, '?')
        line = f"  {flag} {name}: {phase_status}"
        if total:
            line += f"  ({processed}/{total}, 失败 {failed})"
            done_total += processed
        if phase_status == 'in_progress':
            active_phase = name
        print(line)
    print('-' * 55)

    # 粗略估算：in_progress 阶段的已处理量 / 总量
    if active_phase:
        phase = progress['phases'][active_phase]
        total = phase.get('total', phase.get('total_files', 0))
        processed = phase.get('processed', phase.get('processed_files', 0))
        print(f"当前阶段: {active_phase}（{processed}/{total}）")
    else:
        next_phase = get_next_phase()
        if next_phase:
            print(f"下一步: {next_phase}（可对 AI 说「继续整理小说库」）")
        else:
            print("全部阶段已完成，可运行 validate.py 确认最终校验")

    # 失败文件汇总：从输出目录的校验报告读取
    output_dir = progress.get('output_dir', './NovelLibrary_Processed')
    validation = Path(output_dir) / '.organizer_progress' / 'validation_report.json'
    if validation.exists():
        try:
            with open(validation, encoding='utf-8') as f:
                v = json.load(f)
            failed_items = [d for d in v.get('details', []) if not d.get('passed')]
            if failed_items:
                print(f"校验失败文件 ({len(failed_items)}):")
                for item in failed_items[:10]:
                    print(f"  - {item.get('file_path', '?')}: {'; '.join(item.get('issues', []))}")
        except (OSError, ValueError):
            pass

    print('=' * 55)


if __name__ == '__main__':
    main()
