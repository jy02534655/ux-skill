---
name: Novel Library Batch Organizer
description: 批量整理本地小说库。扫描当前目录下的 NovelLibrary 文件夹，分析所有小说文件，根据文件大小、章节格式规范度、文本污染度自动分层，分别用本地脚本或AI辅助处理，输出到 NovelLibrary_Processed 目录，保持原有分类结构。
triggers:
  - 整理小说库
  - 批量整理小说
  - 排版小说
  - 统一章节
  - NovelLibrary 整理
---

# Novel Library Batch Organizer Skill

## 概述

自动整理当前工作目录下的 NovelLibrary/ 文件夹，对所有 .txt 小说文件进行排版和章节名称统一，输出到 NovelLibrary_Processed/，保持原有分类文件夹结构。

核心原则：
- 只读源文件，所有写入仅在输出目录
- 经济优先：规整层零AI调用，半规整层仅AI识别章节标题，混乱层才全文AI处理
- 可恢复：支持断点续传

## AI 角色边界说明

本 Skill 是「指导型 Skill」，AI 的角色是：
1. 指导用户执行本地 Python 脚本
2. 在需要 AI 辅助识别时（半规整层/混乱层），处理用户粘贴的内容并返回结果
3. 解读脚本输出报告，给出下一步建议

AI 无法直接执行本地脚本或访问用户文件系统，所有脚本需要用户在本地终端中手动运行。

## 目录约定

| 目录 | 说明 |
|------|------|
| ./NovelLibrary/ | 源目录（当前工作目录下） |
| ./NovelLibrary_Processed/ | 输出目录（自动创建） |
| ./.organizer_progress/ | 进度文件目录（自动创建） |

## 分层判断标准

扫描阶段对每个文件计算以下指标：

| 指标 | 阈值 | 层级 |
|------|------|------|
| 文件大小 | < 500KB = 轻量，500KB-5MB = 中等，>5MB = 超大 | 影响分块策略 |
| 章节匹配率 | >80% = 规整，50%-80% = 半规整，<50% = 混乱 | 主层级判定 |
| 文本污染度 | <1% = 清洁，1%-5% = 轻度，>5% = 重度 | 调整处理方式 |

最终层级判定（注意边界情况）：
- 规整层：章节匹配率 >80% 且 污染度 <1%，或 章节匹配率 = 0 且 污染度 <1%（无章节短篇）
- 半规整层：章节匹配率 50%-80% 或（污染度 1%-5% 且 章节匹配率 >0）
- 混乱层：章节匹配率 <50% 或 污染度 >5%

## Workflow（用户执行）

### Step 1: 环境准备
- 确保 NovelLibrary/ 文件夹存在于当前目录
- 创建 NovelLibrary_Processed/ 和 .organizer_progress/ 目录

### Step 2: 扫描与分类
用户执行：
python scripts/scan_and_classify.py

AI 读取 .organizer_progress/classification.json 报告，向用户汇报：
- 总文件数
- 各层级分布
- 需要 AI 介入的文件列表

### Step 3: 分层处理

A. 规整层（零AI调用）
用户执行：
python scripts/clean_basic.py --batch
处理完成，AI 确认结果。

B. 半规整层（AI辅助识别）
1. 用户执行提取候选章节：
python scripts/chapter_replace.py --extract --input "文件路径"
2. 用户将候选章节行粘贴给 AI，AI 使用 templates/prompt_chapter.md 处理，返回 JSON 映射表
3. 用户保存映射表为 {书名}_mapping.json，执行替换：
python scripts/chapter_replace.py --apply --input "文件路径" --mapping "映射表路径"

C. 混乱层（AI逐本处理）
1. 用户执行自动分块：
   python scripts/split_chunks.py --input "小说路径" --output_dir "./chunks/书名" --max_chars 80000
2. 用户逐块粘贴给 AI，AI 使用 templates/prompt_clean.md 处理
3. 用户将所有分块放到同一目录，执行合并：
   python scripts/merge_progress.py --merge --chunks_dir "./chunks/书名" --output "./output.txt"
4. 用户执行统一重编号：
   python scripts/renumber.py --input "./output.txt" --output "./final.txt"

D. 超大型文件（>5MB）
- 在 A/B/C 各层中，文件大小作为独立维度
- 规整层+超大：先分块 -> 规整逻辑 -> 合并 -> 重编号
- 半规整+超大：先分块 -> AI 识别标题 -> 合并 -> 重编号
- 混乱+超大：先分块 -> AI 逐块处理 -> 合并 -> 重编号

### Step 4: 校验
用户执行：
python scripts/validate.py --source ./NovelLibrary --output ./NovelLibrary_Processed

AI 读取 .organizer_progress/validation_report.json，向用户汇报校验结果。

## 特殊章节处理策略

- 序章/楔子 -> 保留原名，或转为"第0章 序章"（可选）
- 尾声/后记 -> 保留原名，不参与主编号
- 番外/外传 -> 保留原名，不参与主编号
- 第X卷 第Y章 -> 只保留章级别（第Y章），卷信息保留在正文中

## 可用资源

### 脚本

| 脚本 | 功能 | 依赖 |
|------|------|------|
| scripts/scan_and_classify.py | 扫描目录、编码检测、分层分析、生成报告 | 无 |
| scripts/clean_basic.py | 规整层排版清洗 | 需要 regular_list.json |
| scripts/chapter_replace.py | 提取候选章节 / 根据映射表执行替换 | 需要 AI 返回的映射表 |
| scripts/renumber.py | 合并后统一重新编号（1-N连续） | 需要待编号的文本 |
| scripts/validate.py | 校验最终输出（对比源文件） | 需要源目录和输出目录 |
| scripts/merge_progress.py | 合并分块结果，恢复断点 | 需要分块文件和进度文件 |

### AI 提示词模板

| 模板 | 用途 |
|------|------|
| templates/prompt_chapter.md | 章节识别：输入候选行，输出映射表 |
| templates/prompt_clean.md | 全文清洗：输入片段，输出排版文本 |

## 异常处理

| 异常 | 处理方式 |
|------|----------|
| 编码检测失败 | 依次尝试 UTF-8 -> GBK -> Big5 -> ANSI |
| 分块时切断章节 | 回溯到最近的章节标题再切分 |
| AI 返回格式错误 | 重试3次，仍失败则标记异常并跳过 |
| 输出字符数变化 >5% | 标记异常，保留原样不输出 |
| 进度文件损坏 | 扫描已处理的输出目录重建进度 |
| 脚本执行失败 | 记录错误日志，继续处理下一个文件 |