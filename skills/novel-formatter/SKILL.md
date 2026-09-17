---
name: Novel Library Batch Organizer
description: 批量整理本地小说库。先统一转码所有文件到 UTF-8 临时目录，再扫描分析、分层处理，最终输出到 NovelLibrary_Processed/ 保持原目录结构。支持断点续传。
triggers:
  - 整理小说库
  - 批量整理小说
  - 排版小说
  - 统一章节
  - 继续整理小说库
  - NovelLibrary 整理
---

# Novel Library Batch Organizer Skill

## 这是什么（30 秒了解）

把本地 TXT 小说库批量整理成统一排版：自动转码（GBK/Big5 → UTF-8）、识别并标准化各种章节标题格式、清理广告与乱码，最终输出到 `NovelLibrary_Processed/`，**源文件永不修改**。

处理分三步：**统一转码 → 扫描分层 → 分层处理**，最后**校验**。
分层是为了省钱：干净规整的书零 AI 处理，只有半规整和混乱的书才动用 AI。

核心原则：
- 源文件只读，永不修改
- 统一编码后再处理，逻辑简洁可靠
- 经济优先：规整层零AI调用，半规整层优先自动映射，仅对杂糅候选使用 AI 识别，混乱层才全文 AI 处理
- 可恢复：支持断点续传（全局进度文件统一管理），中断后说一句「继续整理小说库」即可接着跑

## ⭐ 新手快速上手（5 分钟跑通）

不想看完整文档？只处理大多数规整文件，照下面做即可。

**前置准备（一次性）**
1. 安装 Python 3.8+（已有可跳过）
2. 安装依赖：`pip install chardet`
3. 把小说 `.txt` 文件放入 `./NovelLibrary/`（可含子目录）

**跑 4 条命令（在 Skill 目录下执行）**

```bash
python scripts/preprocess_encoding.py --source ./NovelLibrary --temp ./NovelLibrary_Temp --force
python scripts/scan_and_classify.py --source ./NovelLibrary_Temp --output ./NovelLibrary_Processed
python scripts/clean_basic.py --batch
python scripts/validate.py --source ./NovelLibrary_Temp --output ./NovelLibrary_Processed
```

**完成标志**：最后一条命令显示「校验完成」，打开 `./NovelLibrary_Processed/` 即可看到整理好的书。

**然后**：把第 2 条命令的扫描报告（规整层/半规整层/混乱层数量）贴给 AI，AI 会指导你继续处理半规整层和混乱层的文件——这两层**必须**走 AI 协助流程，不能用 `clean_basic.py --batch` 跳过，否则标题格式、广告过滤会出质量问题。

## 什么时候用 / 怎么跟 AI 说

**适合的场景**：本地有一批 TXT 小说，想统一排版、统一章节格式、过滤广告，或从旧编码乱码中恢复。

**怎么触发**：直接用下面的话术告诉 AI 即可，不需要记命令：

| 场景 | 对 AI 说的话 |
|---|---|
| 首次整理 | 「帮我整理小说库」/「把 NovelLibrary 里的书排版一下」/「统一章节格式」 |
| 继续中断的任务 | 「继续整理小说库」（AI 会读取进度文件，从断点续跑） |
| 查询进度 | 「整理到哪了？」 |
| 脚本报错 | 把终端报错原文直接贴给 AI，例如「scan 报错：源目录不存在」 |
| 中途卡住/超时 | 「刚才处理到 X 文件时断网了/超时了，帮我看看进度」 |

**分工说明**（本 Skill 是「指导型 Skill」）：
- **AI 负责**：给出命令、解读报告、在需要 AI 识别时处理你粘贴的内容、告诉你下一步做什么
- **你负责**：在本地终端运行 AI 给的命令，把脚本输出/报错贴给 AI

## 处理效果示例

**1. 转码（乱码 → 正常）**

转码前（GBK 文件直接当 UTF-8 打开）：
```text
锟斤拷锟斤拷锟斤拷 第一章 风云再起 锟斤拷...
```
转码后（输出统一 UTF-8）：
```text
第一章 风云再起
```

**2. 章节标题标准化（各种格式 → 统一「第N章 标题」）**

| 原始 | 处理后 |
|---|---|
| 第一章 初入江湖 | 第1章 初入江湖 |
| Chapter 5 | 第5章 |
| （3） | 第3章 |
| （十二） | 第12章 |
| 三、偶遇 | 第3章 偶遇 |
| 第一集：初遇 | 第1章 初遇 |
| 序章 / 楔子 / 尾声 / 番外 | 保留原名，不参与编号 |

**3. 排版（清洗前后）**

处理前：行尾有空格、半角标点、连续空行、段落间无空行
处理后：全角标点统一、段落间 1 个空行、连续空行压缩、行内空格清除

## AI 角色边界

| AI 能做什么 | AI 不能做什么 |
|---|---|
| 指导你执行本地 Python 脚本 | 无法直接访问你的文件系统 |
| 处理你粘贴的章节候选/文本片段（AI 识别） | 无法替你运行脚本（需你在终端执行） |
| 解读脚本输出报告，给出下一步建议 | 无法修改源文件（脚本设计为只读源目录） |

边界细节（容易踩坑的地方）：
- **脚本必须在你的电脑上运行**，AI 只提供命令和解读，不要等待 AI「自动执行」
- 需要 AI 识别的内容（半规整层候选行、混乱层文本块）**由你粘贴**给 AI，AI 返回结果后你再保存并继续
- AI 阶段依赖网络，**长任务建议分批**（见「大库分批处理建议」），避免中途超时

## 目录约定

- `./NovelLibrary/` 源目录（只读）
- `./NovelLibrary_Temp/` 临时目录（统一 UTF-8 编码，可随时清空重建）
- `./NovelLibrary_Processed/` 输出目录（最终结果）
- `./.organizer_progress/` 进度文件目录（全局进度、分层清单、校验报告）

## 完整工作流

### Step 0: 预处理（统一转码）

⚠️ **安全警告**：`--temp` 指定的目录会被**完全清空**（递归删除）！请确认：
- `--temp` 不含任何重要文件
- 不要把 `--temp` 设为 `./NovelLibrary`（源目录）或当前目录 `.`
- 脚本内置安全检查：temp==source、temp 是 source 的子目录/父目录、temp==当前目录、temp==用户主目录 都会拒绝执行
- 清空已有目录前有 5 秒倒计时，可 Ctrl+C 取消

```bash
python scripts/preprocess_encoding.py --source ./NovelLibrary --temp ./NovelLibrary_Temp --force
```

**完成后会看到**：逐文件 `[OK] 文件名 -> 编码` 列表和统计（成功/失败数、编码分布）。编码检测失败的文件会按 UTF-8→GBK→GB18030→Big5 依次尝试。

### Step 1: 扫描与分类

```bash
python scripts/scan_and_classify.py --source ./NovelLibrary_Temp --output ./NovelLibrary_Processed
```

**完成后会看到**：每个文件归入 规整/半规整/混乱/错误 四层之一，以及汇总统计。结果保存在 `NovelLibrary_Processed/.organizer_progress/`（classification.json + 各层清单）。**把这份汇总贴给 AI**，让 AI 安排后续处理顺序。

### Step 2: 分层处理

| 层级 | 处理方式 | 命令/流程 |
|---|---|---|
| A. 规整层 | 零 AI 调用，纯本地清洗 | `python scripts/clean_basic.py --batch` |
| B. 半规整层 | 自动映射优先，杂糅候选送 AI 识别 | `auto_chapter_map.py` + `chapter_replace.py`（按 AI 指导逐文件执行） |
| C. 混乱层 | AI 逐块清洗 | `split_chunks.py` → AI 逐块清洗 → `merge_progress.py` → `renumber.py` |

⚠️ **半规整层和混乱层必须走完整的 AI 处理流程**，不可用批量跳过脚本，否则会导致标题格式混乱、元数据残留、首行非章节等质量问题。

### Step 3: 校验

```bash
python scripts/validate.py --source ./NovelLibrary_Temp --output ./NovelLibrary_Processed
```

**完成后会看到**：通过/失败数量、失败文件列表（含原因）、告警文件列表、质量明细。

报告三类问题：
1. **硬失败**：未规范化标题残留、字符变化>10%、广告残留>5处 → 判为失败
2. **连续性告警**：章节编号不连续（原文固有结构，不影响 pass/fail）
3. **质量告警**：首行非章节、元数据残留、裸标题（不影响 pass/fail）

校验失败的处理：把失败列表贴给 AI，AI 会指出需要重跑哪一步（通常是回到 Step 2 对应层重新处理该文件）。

## 分层判断标准

| 指标 | 取值 |
|---|---|
| 文件大小 | <500KB 轻量，500KB–5MB 中等，>5MB 超大 |
| 章节匹配率 | >80% 规整，50%–80% 半规整，<50% 混乱 |
| 文本污染度 | <1% 清洁，1%–5% 轻度，>5% 重度 |

最终判定（注意边界情况）：
- **规整层**：章节匹配率 >80% 且污染度 <1%；或章节匹配率 =0 且污染度 <1%（无章节短篇）
- **半规整层**：章节匹配率 50%–80%；或（污染度 1%–5% 且章节匹配率 >0）
- **混乱层**：章节匹配率 <50%；或污染度 >5%

> 统计口径：章节匹配率 = **疑似标题行（短行，<60 字符）中可识别格式的比例**。正文长行不参与计算，否则真实小说的匹配率会被正文稀释到永远无法命中规整层，导致所有书都被迫走 AI。

## 章节标题规范化规则

以下格式全部自动识别并统一转为「第N章」（单位统一转为 `章`，保留原编号，不重新编号）：

| 原始格式 | 转换后 | 示例 |
|---|---|---|
| 第X章/回/节 标题 | 保留 | 第3章 初次相遇 |
| 第一章/回/节 | 中文数字转阿拉伯 | 第一章 → 第1章 |
| Chapter X / CHAPTER X | 第X章 | Chapter 5 → 第5章 |
| （N）/ (N) | 第N章 | （3）→ 第3章 |
| （一）（二）（三）... | 第1章 第2章 第3章 | （一）→ 第1章 |
| 【N、标题】/【N，标题】 | 第N章 标题 | 【1、初次相遇】→ 第1章 初次相遇 |
| 一、标题 / 1、标题 | 第1章 标题 | 一、初次相遇 → 第1章 初次相遇 |
| 第一集/卷/部：标题 | 第1章 标题 | 第一集：初遇 → 第1章 初遇 |
| 正文 第一章... | 剥离前缀后转换 | 正文 第一章芙蓉出水 → 第1章 芙蓉出水 |
| 书名（N） | 保留为章节标题 | 楠楠的暴露（五）→ 第5章 |
| 第N话/第X话 | 第N章 | 第100话 → 第100章 |
| 章 N（无「第」前缀） | 第N章 | 章 100 → 第100章 |
| Section N / Part N | 第N章 | Section 1 → 第1章 |

**特殊章节**（不参与编号，保留原名）：序章 / 楔子 / 第零章 / 引子 / 前言 / 引言 / 尾声 / 后记 / 番外 / 外传 / 跋

**转换规则**
1. 只做格式转换，不重新编号（保留原文的章节数字；混乱层合并后才由 renumber.py 统一编号）
2. 中文数字一律转阿拉伯数字（一→1，十→10，支持到万级如 第一万章 → 第10000章）
3. 装饰前缀（☆、※、正文 等）自动剥离
4. 章节单位（集/卷/部/回）统一转为「章」
5. 每章标题独占一行，正文段落间用 1 个空行分隔

## 脚本与模板清单

| 脚本 | 作用 |
|---|---|
| `preprocess_encoding.py` | 统一转码所有文件到 UTF-8（Step 0） |
| `scan_and_classify.py` | 扫描、分层分析、生成报告（Step 1） |
| `clean_basic.py` | 规整层排版清洗 + 章节标题标准化（支持全部 10 种格式） |
| `chapter_replace.py` | 提取候选章节 / 根据映射表执行替换 |
| `auto_chapter_map.py` | 半规整层自动映射（零 AI 处理） |
| `split_chunks.py` | 按章节边界自动分块（每块默认 80000 字符） |
| `renumber.py` | 合并后统一重新编号（1–N 连续） |
| `merge_progress.py` | 合并分块结果，恢复断点 |
| `progress_manager.py` | 全局进度管理（原子写入 + 文件锁 + 自动备份；`--reset` 强制重置） |
| `progress_report.py` | 进度报告：各阶段完成率、失败文件、下一步建议（`python scripts/progress_report.py`） |
| `validate.py` | 校验最终输出（标题格式、连续性、质量、广告） |
| `chapter_patterns.py` | 公共正则模块，所有脚本依赖 |

AI 提示词模板：`templates/prompt_chapter.md`（章节识别）、`templates/prompt_clean.md`（全文清洗）。

## 进度保存与断点续传

位置：`.organizer_progress/task_progress.json`，记录每个阶段的 status（pending / in_progress / completed / failed）和已处理量。

结构：`phases` 包含六个阶段：`preprocess` → `scan` → `regular_layer` → `semi_regular_layer` → `chaotic_layer` → `validate`，各段记录 `total` / `processed` / `failed` 与当前文件。

当你（或 AI）说「**继续整理小说库**」时：
1. 读取进度文件
2. `completed` → 跳过；`in_progress` → 从该阶段断点继续；`pending` → 开始执行；`failed` → 先检查错误
3. 全部完成后 status 更新为 `completed`

中途处理（网络/AI 超时、关电脑、误关窗口）都不怕，重跑对应命令即可，脚本会自动续传。**不要删除 `.organizer_progress/` 目录**，否则失去断点。

进度文件每次更新前会自动备份上一版本到 `task_progress.json.bak`（损坏时可手工恢复）；彻底重开任务用 `python scripts/progress_manager.py --reset`，自动清除并重建进度，不需要手动删文件。

## 大库分批处理建议

大批量（>100 本或 >1GB）建议分批，降低网络/AI 超时风险：

- **按子目录分批**：把源库按作者/分类拆成多个子目录，每批尽量 <100 本、<1GB，一批跑完整流程后再跑下一批（每批独立使用自己的 source/temp/output 目录）
- **AI 阶段小批**：半规整层/混乱层的 AI 识别按文件逐个进行，建议每批 10–20 本，中间休息；连续超时就把报错贴给 AI 调整
- **中断无损失**：分批跑、中途停都没关系，进度都在 `.organizer_progress/`，下次说「继续整理小说库」即可
- 单个文件连续 3 次 AI 失败会被标记 failed 跳过（见 ai_errors.log），**不会阻塞整批**

## FAQ 常见问题与错误信息解读

### 环境与安装

**Q: 报 `ModuleNotFoundError: No module named 'chardet'`**
A: 未安装依赖。运行 `pip install chardet` 后重试。

**Q: 报 `python 不是内部或外部命令`**
A: Python 未加入 PATH。重新安装 Python 时勾选「Add Python to PATH」，或在终端用完整路径（如 `py scripts/...`）运行。

### 命令与顺序

**Q: 报「源目录不存在: ./NovelLibrary」 / 「临时目录不存在」**
A: 目录名不对，或还没建目录。确认 `./NovelLibrary/` 存在且含 `.txt` 文件；Step 1 前必须先完成 Step 0。

**Q: 报「临时目录不能是源目录的子目录/父目录」或「路径是根目录，禁止操作」**
A: `--temp` 与 `--source` 路径重叠，或 `--temp` 指向了盘符根目录。换一个独立目录名（如 `./NovelLibrary_Temp`）即可。这是安全保护，不是 bug。

**Q: 报「未找到规整层清单」或「未找到分类报告，请先运行 scan_and_classify.py」**
A: 步骤顺序错了。先跑 Step 1（scan_and_classify.py）生成分类报告和层清单，再跑 Step 2/3。也可能是 `.organizer_progress/` 被删了，需重跑 Step 1。

**Q: 报「获取锁超时」**
A: 进度文件被占用：之前有脚本还在运行，或窗口没关完。关掉多余的终端窗口，等几秒重跑同一命令即可。

### 处理结果问题

**Q: 校验显示「未规范化的标题残留」**
A: 该文件走错了处理路径——半规整/混乱层的文件用了 `clean_basic.py --batch` 跳过。回到 Step 2 按正确流程重新处理该文件。

**Q: 校验显示「字符数变化率超过 10%」**
**Q: 某个文件处理失败（FAIL）**
A: 这是保护机制，防止内容被破坏。单文件失败不会中断整体。把失败信息贴给 AI，通常重跑该文件的处理步骤即可；持续失败看 `.organizer_progress/ai_errors.log`。

**Q: 输出里还有广告/网址**
A: 确认该文件属于哪一层。规整层广告>5处会被校验判失败并列出；半规整/混乱层需走 AI 清洗流程。广告关键词库见 `references/pollution_patterns.md`。

**Q: 转码后仍是乱码（�、锟斤拷、烫烫烫）**
A: 文件编码特殊或已损坏。脚本会按 UTF-8→GBK→GB18030→Big5 依次尝试，全部失败则替换为 � 并记录位置；乱码比例高会被标记 heavy_pollution（参见 `references/encoding_guide.md`）。把该文件的行首内容贴给 AI 人工判断。

**Q: 章节编号不连续 / 首行非章节 / 裸标题**
A: 这些是告警不是失败。编号不连续多为原文固有结构（如分卷序号）；首行非章节可通过 AI 清洗修正；裸标题（第N章后无内容）是原文如此，可忽略或由 AI 处理。

**Q: 处理完效果不满意，想重来**
A: 源文件一直没动。清空 `NovelLibrary_Temp` 和 `NovelLibrary_Processed`（或换输出目录名），从 Step 0 重跑即可。

### 断点与进度

**Q: 进度文件损坏/被误删**
A: 脚本会扫描已处理输出目录重建进度。也可以从头重跑：`NovelLibrary_Processed` 里已是最终结果的文件不影响。

**Q: AI 阶段反复超时/返回格式错误**
A: 单个文件最多重试 3 次，建议按**指数退避**节奏：第 1 次失败立即重试 → 第 2 次等 30 秒 → 第 3 次等 2 分钟，仍失败标记 failed 并跳过，错误记录在 `.organizer_progress/ai_errors.log`，不阻塞整体。重试仍失败就把日志贴给 AI 分析（通常是内容太杂，需要调整分块大小，`split_chunks.py --max_chars` 可调）。

## 能力边界明细

- **只处理 `.txt` 文件**：epub / docx / pdf / txt 压缩包不直接支持，需先自行转为 txt 再放入源目录
- **不修改源文件**：`NovelLibrary/` 只读，所有改动发生在 Temp/Processed 目录
- **不做内容校对**：不修正错别字、不改剧情、不做敏感内容审查，只做排版与格式
- **繁体不转简体**：Big5 繁体会转码为 UTF-8 但保留繁体字形
- **不识别图片/扫描件**：手写或扫描版小说无法处理
- **不重新编号**：规整/半规整层保留原文编号；仅混乱层合并后可统一编号
- **需要人类在场**：AI 识别环节需要你与 AI 一来一回粘贴内容，无法全自动无人值守
- **进度目录不可删**：`.organizer_progress/` 是断点续传的依据

## 运行环境与依赖

- Python 3.8+（脚本使用标准库 + chardet）
- 安装：`pip install chardet`
- 脚本同时兼容 Windows（msvcrt 文件锁）与 Linux/macOS（fcntl）
- 所有脚本均从 Skill 目录（含 `scripts/` 与 `.organizer_progress/` 的上级目录）运行

## 异常处理总览

| 异常 | 处理方式 |
|---|---|
| 编码检测失败 | 依次尝试 UTF-8 → GBK → GB18030 → Big5 |
| 分块切断章节 | 回溯到最近的章节标题再切分 |
| AI 返回格式错误 | 重试 3 次，仍失败则标记异常并跳过 |
| 输出字符数变化 >5% | 标记异常，保留原样不输出 |
| 进度文件损坏 | 扫描已处理的输出目录重建进度 |
| 脚本执行失败 | 记录错误日志，继续处理下一个文件 |
