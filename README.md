# UX Skill 工具集

小说库批量整理工具集 — 将杂乱的 TXT 小说库自动排版、标准化章节、统一编码。

## 目录

- [概述](#概述)
- [新手入门（5 分钟跑通）](#新手入门5-分钟跑通)
- [前置要求](#前置要求)
- [快速开始](#快速开始)
- [工作流](#工作流)
- [脚本清单](#脚本清单)
- [目录约定](#目录约定)
- [分层标准](#分层标准)
- [章节标题规范化](#章节标题规范化)
- [进度恢复](#进度恢复)
- [避坑指南](#避坑指南)
- [FAQ](#faq)

---

## 概述

本工具集采用三阶段流水线处理小说库：

```
统一转码(Step 0) → 扫描分层(Step 1) → 分层处理(Step 2) → 校验(Step 3)
```

1. **预处理** — 遍历源目录，检测编码，统一转为 UTF-8
2. **分层处理** — 按文件整洁度分四层，逐层自动化处理
3. **输出** — 输出排版后的小说，保持原目录结构

一句话理解：**先把所有书变成统一的 UTF-8，再按“干不干净”分四堆，干净的全自动处理，不干净的人工/AI 协助处理，最后统一验收。**

核心原则：
- **源文件只读**，永不修改原文件
- **经济优先**：规整层零 AI 调用，半规整层优先自动映射，混乱层才用 AI
- **可恢复**：支持断点续传，意外中断后可继续

## 新手入门（5 分钟跑通）

第一次使用？只想先处理大多数规整文件？照做即可：

1. **准备**：安装 Python 3.8+（已有可跳过）；`pip install chardet`；把小说 `.txt` 放进 `./NovelLibrary/`（可含子目录）
2. **跑 4 条命令**（在仓库根目录执行）：

```bash
python skills/novel-formatter/scripts/preprocess_encoding.py --source ./NovelLibrary --temp ./NovelLibrary_Temp --force
python skills/novel-formatter/scripts/scan_and_classify.py --source ./NovelLibrary_Temp --output ./NovelLibrary_Processed
python skills/novel-formatter/scripts/clean_basic.py --batch
python skills/novel-formatter/scripts/validate.py --source ./NovelLibrary_Temp --output ./NovelLibrary_Processed
```

3. **完成标志**：最后一条命令输出「校验完成」；打开 `./NovelLibrary_Processed/` 即为整理好的书
4. **接下来**：把第 2 条命令的扫描汇总（规整/半规整/混乱层数量）给 AI，让 AI 指导半规整层和混乱层的处理——这两层**必须**走 AI 协助流程，不能用 `clean_basic.py --batch` 跳过

**处理前后对比示例**：

| 项目 | 处理前 | 处理后 |
|---|---|---|
| 编码 | GBK 乱码（锟斤拷/�） | UTF-8 正常中文 |
| 章节标题 | 第一章 / Chapter 5 / （3）/ 三、偶遇 | 统一「第N章 标题」 |
| 排版 | 半角标点、连续空行、行尾空格 | 全角标点、段落间 1 空行、无行内空格 |
| 广告 | 「求收藏」「关注公众号」混在正文 | 常规过滤（残留>5处会被校验判失败） |

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

> 统计口径：章节匹配率 = **疑似标题行（短行，<60 字符）中可识别格式的比例**。正文长行不参与计算，否则真实小说的匹配率会被正文稀释，永远无法命中规整层。

**我的文件属于哪一层？（决策树）**

```
文件能被识别出章节标题吗？
├─ 不能（匹配率 = 0）且无污染 → 规整层（无章节短篇，自动排版）
├─ 能：标题格式统一、无广告乱码 → 规整层（零 AI）
├─ 能：格式杂糅（几个格式混用）或有轻度污染 → 半规整层（自动映射 + 必要时 AI）
└─ 能/不能：格式基本认不出 或 污染重（广告、乱码多）→ 混乱层（AI 逐块清洗）
```

**边界情况处理规则**：
- 匹配率刚好 50%：落入半规整层（`50%–80%` 含 50%）
- 污染度刚好 5%：不满足「污染度 < 5%」的半规整条件，落入混乱层（保守处理，交给 AI）
- 匹配率 = 0 的短篇：只要污染度 < 1% 就按规整层处理（无章节但干净）
- 污染度 = 0 但匹配率 < 50%：格式基本认不出 → 混乱层（有章节但无法自动识别，需 AI）

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
| 第N话/第X话 | 第N章 | 第100话 → 第100章 |
| 章 N（无「第」前缀） | 第N章 | 章 100 → 第100章 |
| Section N / Part N | 第N章 | Section 1 → 第1章 |

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
| `progress_manager.py` | 全局进度管理（被各脚本调用，自动备份；`--reset` 强制重置） | — |
| `progress_report.py` | 查看各阶段完成率、失败文件、下一步建议 | `--status` |
| `validate.py` | 校验最终输出质量 | `--source`, `--output` |
| `chapter_patterns.py` | 公共正则模块（被各脚本引用） | — |

## 进度恢复

全局进度文件位于 `.organizer_progress/task_progress.json`，记录每个阶段的完成状态。意外中断后，重新运行脚本会自动检测断点，跳过错过的阶段从断点继续。

进度文件每次更新前会自动备份上一版本到 `task_progress.json.bak`；彻底重开任务用 `python skills/novel-formatter/scripts/progress_manager.py --reset`，不需要手动删文件。

## 异常处理

| 异常场景 | 处理方式 |
|---------|---------|
| 编码检测失败 | 依次尝试 UTF-8 → GBK → GB18030 → Big5 |
| 分块切断章节 | 回溯到最近章节标题再切分 |
| AI 返回格式错误 | 重试 3 次，仍失败则标记异常并跳过 |
| 输出字符变化 > 5% | 标记异常，保留原样不输出 |
| 进度文件损坏 | 扫描已处理的输出目录重建进度 |
| 脚本执行失败 | 记录错误日志，继续处理下一个文件 |

## 避坑指南

以下错误都是实际使用中最常见的，照着检查就能解决：

1. **不要把 `--temp` 设成源目录或当前目录**：临时目录会被递归清空，脚本有安全检查会拒绝（报「临时目录不能是源目录的子目录/父目录」「路径是根目录，禁止操作」等），但请自觉使用独立目录名（如 `./NovelLibrary_Temp`）
2. **不要跳过分层**：半规整/混乱层的文件用 `clean_basic.py --batch` 批量跳过会导致标题格式混乱、元数据残留，校验会判失败——这两层必须走 AI 协助流程
3. **不要手动修改/删除 `.organizer_progress/`**：断点续传的依据；删了就得从扫描重新开始。想重开用 `progress_manager.py --reset`
4. **步骤顺序不能颠倒**：必须先 Step 0 转码 → Step 1 扫描 → Step 2 处理 → Step 3 校验。报「未找到规整层清单/分类报告」就是顺序错了
5. **大文件库分批处理**：>100 本或 >1GB 建议按子目录分批（每批 <100 本、<1GB），AI 阶段每批 10–20 本，降低网络/AI 超时风险；中断后说「继续」即可续传
6. **AI 阶段反复超时**：按指数退避重试（立即 → 30 秒 → 2 分钟），单文件最多 3 次，失败会标记跳过并记录到 `ai_errors.log`，不阻塞整体
7. **编码乱码残留**：脚本按 UTF-8→GBK→GB18030→Big5 依次尝试；仍乱码（�/锟斤拷/烫烫烫）的文件多半已损坏，把行首内容贴给 AI 人工判断
8. **进度文件损坏**：脚本会扫描已处理输出目录重建进度；或从 `task_progress.json.bak` 手工恢复

## FAQ

**Q: 需要安装什么依赖？**
A: 仅 `chardet`。运行 `pip install chardet` 即可。

**Q: 源文件会被修改吗？**
A: 不会。源目录 `NovelLibrary/` 全程只读，所有操作在临时目录和输出目录进行。

**Q: 处理到一半中断了怎么办？**
A: 重新执行对应步骤即可。进度文件会自动检测已完成部分，跳过已处理的文件继续未完成的。

**Q: 半规整层必须用 AI 吗？**
A: 优先尝试 `auto_chapter_map.py` 自动映射。如果候选行格式复杂自动映射失败，才需要 AI 辅助识别。

**Q: 处理一批大概要多久？**
A: 取决于库大小和分层结果：规整层纯本地脚本，几乎秒级/分钟级；半规整和混乱层涉及 AI 交互，每个文件几分钟到几十分钟不等。可以先跑 Step 1 看各层数量再估算。

**Q: 需要多少磁盘空间？**
A: 建议预留源库体积的 3 倍：源目录 + 临时目录（UTF-8 转码后通常更大）+ 输出目录。

**Q: 什么时候会调用 AI？**
A: 只在半规整层自动映射失败和混乱层逐块清洗时；规整层零 AI。

**Q: 怎么跳过某个文件不处理？**
A: 处理前把该文件移出源目录即可；或用 `progress_manager.py --reset` 后只放入要处理的文件。

**Q: 想重新处理某一本书怎么办？**
A: 源文件没被改动。删掉输出目录里对应文件（及 Temp 里的对应文件），重跑该层处理命令即可；或从 Step 0 重跑。

**Q: 编码检测失败会怎样？**
A: 脚本按 UTF-8→GBK→GB18030→Big5 依次尝试解码；全部失败则用忽略错误模式读取并替换为 �，同时记录位置；乱码比例高的文件会被标记重度污染（见 `references/encoding_guide.md`）。

**Q: 章节识别失败怎么办？**
A: 半规整层自动映射失败时，用 `chapter_replace.py --extract` 提取候选行贴给 AI 识别；混乱层用 `split_chunks.py` 分块后逐块让 AI 清洗。

**Q: 校验失败的文件怎么处理？**
A: 查看失败原因：标题残留 → 回到 Step 2 按正确流程重处理该文件；字符变化>10% → 保护机制触发，重跑该文件；广告残留 → 确认是否走了 AI 清洗。

**Q: 超大的文件（>5MB）能处理吗？**
A: 能，但建议调整 `split_chunks.py --max_chars`（默认 80000 字符）控制每块大小，避免 AI 上下文溢出；内存方面 Python 处理几 MB 文本没有问题。