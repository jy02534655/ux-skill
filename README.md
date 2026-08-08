# UX Skill 工具集

小说库批量整理工具集 — 将杂乱的 TXT 小说库自动排版、标准化章节、统一编码。

## 目录

- [概述](#概述)
- [前置要求](#前置要求)
- [快速开始](#快速开始)
- [工作流](#工作流)
- [脚本清单](#脚本清单)
- [目录约定](#目录约定)
- [分层标准](#分层标准)
- [章节标题规范化](#章节标题规范化)
- [FAQ](#faq)

---

## 概述

本工具集采用三阶段流水线处理小说库：

1. **预处理** — 遍历源目录，检测编码，统一转为 UTF-8
2. **分层处理** — 按文件整洁度分四层，逐层自动化处理
3. **输出** — 输出排版后的小说，保持原目录结构

核心原则：
- **源文件只读**，永不修改原文件
- **经济优先**：规整层零 AI 调用，半规整层优先自动映射，混乱层才用 AI
- **可恢复**：支持断点续传，意外中断后可继续

## 前置要求

- Python 3.8+
- 依赖：`chardet`（编码检测）

```bash
pip install chardet
```

## 快速开始

```bash
# 1. 预处理：统一编码
python skills/novel-formatter/scripts/preprocess_encoding.py \
    --source ./NovelLibrary \
    --temp ./NovelLibrary_Temp

# 2. 扫描分类
python skills/novel-formatter/scripts/scan_and_classify.py \
    --source ./NovelLibrary_Temp \
    --output ./NovelLibrary_Processed

# 3. 规整层处理
python skills/novel-formatter/scripts/clean_basic.py --batch

# 4. 半规整层（自动映射）
python skills/novel-formatter/scripts/auto_chapter_map.py \
    --input "NovelLibrary_Temp/分类/书名.txt"
python skills/novel-formatter/scripts/chapter_replace.py \
    --apply --input "NovelLibrary_Temp/分类/书名.txt" \
    --mapping mapping.json

# 5. 混乱层（AI 辅助）
python skills/novel-formatter/scripts/split_chunks.py \
    --input "NovelLibrary_Temp/分类/书名.txt" \
    --output_dir ./chunks
# → AI 逐块清洗后 →
python skills/novel-formatter/scripts/merge_progress.py \
    --merge --chunks_dir ./chunks --output ./merged.txt
python skills/novel-formatter/scripts/renumber.py \
    --input merged.txt --output final.txt

# 6. 校验
python skills/novel-formatter/scripts/validate.py \
    --source ./NovelLibrary_Temp \
    --output ./NovelLibrary_Processed
```

## 工作流

### Step 0: 预处理（统一编码）

```bash
python scripts/preprocess_encoding.py \
    --source ./NovelLibrary \
    --temp ./NovelLibrary_Temp \
    [--force]
```

- 遍历 `NovelLibrary/` 下所有 `.txt` 文件
- 用 `chardet` 检测编码，统一转为 UTF-8 无 BOM
- 输出到 `NovelLibrary_Temp/`，保持目录结构
- `--force`：清空已有临时目录再执行

> ⚠️ `--temp` 目录会被完全清空，确认不含重要文件后再执行！

### Step 1: 扫描与分类

```bash
python scripts/scan_and_classify.py \
    --source ./NovelLibrary_Temp \
    --output ./NovelLibrary_Processed
```

为每个文件计算：
- **章节匹配率**：标题行占比
- **文本污染度**：异常字符 + 广告关键词
- 按规则分层：规整 / 半规整 / 混乱 / 错误

### Step 2: 分层处理

| 层级 | 处理方式 | 脚本 |
|------|---------|------|
| 规整层 | 纯本地排版 + 章节标准化 | `clean_basic.py --batch` |
| 半规整层 | 自动提取候选行 → AI 识别 → 映射替换 | `chapter_replace.py` + `auto_chapter_map.py` |
| 混乱层 | 按章节分块 → AI 逐块清洗 → 合并 → 重编号 | `split_chunks.py` → `merge_progress.py` → `renumber.py` |

### Step 3: 校验

```bash
python scripts/validate.py \
    --source ./NovelLibrary_Temp \
    --output ./NovelLibrary_Processed
```

报告三类问题：
1. **硬失败**：标题残留非标准格式、字符变化 > 10%、广告残留 > 5 处
2. **连续性告警**：章节编号不连续（不判定 pass/fail）
3. **质量告警**：首行非章节、元数据残留、裸标题

## 目录约定

| 目录 | 用途 |
|------|------|
| `./NovelLibrary/` | 源目录（只读，不修改） |
| `./NovelLibrary_Temp/` | 临时目录（UTF-8 编码） |
| `./NovelLibrary_Processed/` | 输出目录（最终结果） |
| `./.organizer_progress/` | 进度文件、日志 |

## 分层标准

扫描阶段计算三项指标：

- **文件大小**：<500KB = 轻量，500KB–5MB = 中等，>5MB = 超大
- **章节匹配率**：>80% = 规整，50%–80% = 半规整，<50% = 混乱
- **文本污染度**：<1% = 清洁，1%–5% = 轻度，>5% = 重度

最终分层（注意边界情况）：

| 层级 | 条件 |
|------|------|
| 规整层 | 匹配率 > 80% 且 污染度 < 1%，或 匹配率 = 0 且 污染度 < 1%（无章节短篇） |
| 半规整层 | 匹配率 50%–80%，或（污染度 1%–5% 且 匹配率 > 0） |
| 混乱层 | 匹配率 < 50% 或 污染度 > 5% |

## 章节标题规范化

脚本自动识别并转换以下格式（所有单位统一转为 `章`）：

| 原始格式 | 转换后 | 示例 |
|---------|--------|------|
| 第X章/回/节 标题 | 保留 | 第3章 初次相遇 |
| 第一章/回/节 | 中文数字转阿拉伯 | 第一章 → 第1章 |
| Chapter X / CHAPTER X | 第X章 | Chapter 5 → 第5章 |
| （N）/ (N) | 第N章 | （3）→ 第3章 |
| （一）（二）... | 第1章 第2章 ... | （一）→ 第1章 |
| 【N、标题】/ 【N，标题】 | 第N章 标题 | 【1、初次相遇】→ 第1章 初次相遇 |
| 一、标题 / 1、标题 | 第1章 标题 | 一、初次相遇 → 第1章 初次相遇 |
| 第一集/卷/部：标题 | 第1章 标题 | 第一集：初遇 → 第1章 初遇 |
| 正文 第一章... | 剥离前缀后转换 | 正文 第一章芙蓉出水 → 第1章 芙蓉出水 |
| N） | 第N章 | 5）→ 第5章 |

**特殊章节**（保留原名，不参与编号）：
- 序章 / 楔子 / 第零章 / 引子 / 前言 / 引言
- 尾声 / 后记 / 番外 / 外传 / 跋

**转换规则**：
1. 只做格式转换，不重新编号（保留原文数字）
2. 中文数字一律转为阿拉伯数字
3. 装饰前缀（☆、※、正文 等）自动剥离
4. 单位（集/卷/部/回）统一转为"章"
5. 每章标题独占一行，正文段落间用 1 个空行分隔

## 脚本清单

| 脚本 | 用途 | 关键参数 |
|------|------|---------|
| `preprocess_encoding.py` | 统一转码所有文件到 UTF-8 | `--source`, `--temp`, `--force` |
| `scan_and_classify.py` | 扫描、分层分析、生成报告 | `--source`, `--output` |
| `clean_basic.py` | 规整层排版 + 章节标准化 | `--batch`, `--source`, `--output_dir` |
| `chapter_replace.py` | 提取候选章节 / 按映射表替换 | `--extract`, `--apply`, `--input`, `--mapping` |
| `auto_chapter_map.py` | 半规整层自动映射（零 AI） | `--input`, `--output` |
| `split_chunks.py` | 按章节边界分块 | `--input`, `--output_dir`, `--max_chars` |
| `merge_progress.py` | 合并分块结果 + 断点续传 | `--merge`, `--status`, `--chunks_dir` |
| `renumber.py` | 合并后统一编号 1–N | `--input`, `--output` |
| `progress_manager.py` | 全局进度管理（被各脚本调用） | — |
| `validate.py` | 校验最终输出质量 | `--source`, `--output` |
| `chapter_patterns.py` | 公共正则模块（被各脚本引用） | — |

## 进度恢复

全局进度文件位于 `.organizer_progress/task_progress.json`，记录每个阶段的完成状态。意外中断后，重新运行脚本会自动检测断点，跳过错过的阶段从断点继续。

## 异常处理

| 异常场景 | 处理方式 |
|---------|---------|
| 编码检测失败 | 依次尝试 UTF-8 → GBK → GB18030 → Big5 |
| 分块切断章节 | 回溯到最近章节标题再切分 |
| AI 返回格式错误 | 重试 3 次，仍失败则标记异常并跳过 |
| 输出字符变化 > 5% | 标记异常，保留原样不输出 |
| 进度文件损坏 | 扫描已处理的输出目录重建进度 |
| 脚本执行失败 | 记录错误日志，继续处理下一个文件 |

## FAQ

**Q: 需要安装什么依赖？**
A: 仅 `chardet`。运行 `pip install chardet` 即可。

**Q: 源文件会被修改吗？**
A: 不会。源目录 `NovelLibrary/` 全程只读，所有操作在临时目录和输出目录进行。

**Q: 处理到一半中断了怎么办？**
A: 重新执行对应步骤即可。进度文件会自动检测已完成部分，跳过已处理的文件继续未完成的。

**Q: 半规整层必须用 AI 吗？**
A: 优先尝试 `auto_chapter_map.py` 自动映射。如果候选行格式复杂自动映射失败，才需要 AI 辅助识别。