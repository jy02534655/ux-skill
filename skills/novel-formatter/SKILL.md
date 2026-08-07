---
name: Novel Library Batch Organizer
description: 批量整理本地小说库。扫描当前目录下的 NovelLibrary 文件夹，分析所有小说文件，根据文件大小、章节格式规范度、文本污染度自动分层，分别用本地脚本或AI辅助处理，输出到 NovelLibrary_Processed 目录，保持原有分类结构。
triggers:
  - 整理小说库
  - 整理小说
  - 批量整理
  - NovelLibrary
  - 排版小说
  - 统一章节
---

# Novel Library Batch Organizer Skill

## 概述

自动整理当前工作目录下的 NovelLibrary/ 文件夹，对其中所有 .txt 小说文件进行排版和章节名称统一，输出到 NovelLibrary_Processed/，保持原有分类文件夹结构。

核心原则：
- 只读源文件，所有写入仅在输出目录
- 经济优先：规整层零AI调用，半规整层仅AI识别章节标题，混乱层才全文AI处理
- 可恢复：支持断点续传

## 目录约定

| 目录 | 说明 |
|------|------|
| ./NovelLibrary/ | 源目录（当前工作目录下） |
| ./NovelLibrary_Processed/ | 输出目录（自动创建） |
| ./.organizer_progress/ | 进度文件目录（自动创建） |

源目录结构示例：

./NovelLibrary/
  ├── 武侠/
  │   ├── 射雕英雄传.txt
  │   └── 天龙八部.txt
  ├── 科幻/
  │   └── 三体.txt
  └── 都市/
      └── 平凡的世界.txt

输出目录保持相同结构：

./NovelLibrary_Processed/
  ├── 武侠/
  │   ├── 射雕英雄传.txt
  │   └── 天龙八部.txt
  ├── 科幻/
  │   └── 三体.txt
  └── 都市/
      └── 平凡的世界.txt

## 分层判断标准

扫描阶段对每个文件计算以下指标：

| 指标 | 阈值 | 层级 |
|------|------|------|
| 文件大小 | < 500KB = 轻量，500KB-5MB = 中等，>5MB = 超大 | 影响分块策略 |
| 章节匹配率 | >80% = 规整，50%-80% = 半规整，<50% = 混乱 | 主层级判定 |
| 文本污染度 | <1% = 清洁，1%-5% = 轻度，>5% = 重度 | 调整处理方式 |

最终层级判定：
- 规整层：章节匹配率 >80% 且 污染度 <1%
- 半规整层：章节匹配率 50%-80% 或 污染度 1%-5%
- 混乱层：章节匹配率 <50% 或 污染度 >5%

## 执行步骤

### 第一阶段：扫描与分类

运行 scripts/scan_and_classify.py：

python scripts/scan_and_classify.py

脚本输出：
- 统计报告（文件数、大小分布、格式分布）
- 分层清单（JSON格式，存于 ./.organizer_progress/classification.json）
- 每个文件的元信息（编码、行数、章节数、匹配率、污染度）

### 第二阶段：分层处理

根据 classification.json 逐层处理：

A. 规整层（零AI调用）
- 使用 clean_basic.py 直接处理：合并空行、清除首尾空格、标点全角转换、章节标题正则替换
- 并行处理，每批10个文件

B. 半规整层（AI辅助识别）
- 脚本 chapter_replace.py 提取候选章节行
- 调用AI（使用模板 templates/prompt_chapter.md）获得映射表
- 脚本执行替换

C. 混乱层（AI逐本处理）
- 按 8-10 万字分块（以章节边界优先）
- 使用 merge_progress.py 与AI配合，逐块调用模板 templates/prompt_clean.md 处理

D. 超大型文件（>5MB）
- 按章节边界分块（每块约10万字）
- 重叠窗口策略：每块前后各保留500字符作为上下文

### 第三阶段：校验与输出

运行 validate.py 校验所有输出文件，生成最终报告。

## 可用资源

### 脚本

| 脚本 | 功能 |
|------|------|
| scripts/scan_and_classify.py | 扫描目录、编码检测、分层分析、生成报告 |
| scripts/clean_basic.py | 规整层排版清洗（空行、空格、标点、正则替换章节） |
| scripts/chapter_replace.py | 根据AI映射表执行章节标题替换 |
| scripts/validate.py | 校验最终输出 |
| scripts/merge_progress.py | 合并分块结果，恢复断点 |

### 参考文档

| 文档 | 内容 |
|------|------|
| references/chapter_patterns.md | 常见章节标题正则表达式全集 |
| references/encoding_guide.md | 编码检测与转换方案 |
| references/pollution_patterns.md | 常见污染字符和广告文本特征库 |

### AI 提示词模板

| 模板 | 用途 | 调用场景 |
|------|------|----------|
| templates/prompt_chapter.md | 章节识别：输入候选行，输出映射表 | 半规整层 |
| templates/prompt_clean.md | 全文清洗：输入片段，输出排版文本 | 混乱层 |
| templates/prompt_validate.md | 校验反馈：输入统计，输出异常标记 | 所有层 |

## 使用方式

用户只需说："整理小说库"

AI 自动：
1. 检查 ./NovelLibrary/ 是否存在
2. 调用扫描脚本生成分层报告
3. 按分层策略依次处理
4. 输出到 ./NovelLibrary_Processed/
5. 生成处理日志

恢复中断：
用户说："继续整理小说库"

AI 读取 ./.organizer_progress/ 下的进度文件，从中断处继续。

## 异常处理

| 异常 | 处理方式 |
|------|----------|
| 编码检测失败 | 依次尝试 UTF-8 -> GBK -> Big5 -> ANSI |
| 分块时切断章节 | 回溯到最近的章节标题再切分 |
| AI 返回格式错误 | 重试3次，仍失败则标记异常并跳过 |
| 输出字符数变化 >5% | 标记异常，保留原样不输出 |
| 进度文件损坏 | 扫描已处理的输出目录重建进度 |