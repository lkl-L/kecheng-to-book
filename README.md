# lecture-materials-to-book

把**课程／讲座资料**（音视频转写稿、讲义 PDF/docx、扫描件）编纂成**书籍**的 Agent Skill：
按课分章或按内容分卷、删废话保知识点，排版成书籍版式，加带页码目录，导出 `docx` + `PDF`。

> 这是一套在实践中跑出来的流水线，不是一个 prompt 模板。核心主张是：**内容靠子代理判断，格式靠脚本保证，每一步都有可复核的硬校验。**
> 与具体领域无关：把方法、脚本、版式规范给你，**错字表、术语表、书目清单由你自己在 `references/` 模板里长出来。**

---

## 适用场景

- 你有一整门课的录音／视频（几十小时，按"课／讲／天"组织），想转成文字稿并编成一本书；
- 你有一个装满讲义的本地目录（PDF / docx / 扫描件），想整理成一本"XX 基础"；
- 你已经有了文字稿，但**排版不行**——标题和正文分不开、段落一坨、页码目录不对；
- 你想把某本书里**成体系的某一支内容整章抽出来**另成一册，正文只留主干；
- 你想把散落各处的**实例／案例**单独编成一本题解式的书。

不适用：从零撰写原创内容（这套流程处理的是"已有素材的整理与成书"）。

---

## 目录结构

```
lecture-materials-to-book/
├── SKILL.md                        # 技能主文档（规范 + 流水线 + 踩坑），装进 skill 目录即可用
├── README.md
├── references/                     # 写作规范模板（三种场景各一份，按需复制改写）
│   ├── STYLE_GUIDE.course.md       # 课程音视频成书
│   ├── STYLE_GUIDE.materials.md    # 本地资料（讲义 + 扫描件 OCR）成书
│   └── STYLE_GUIDE.cases.md        # 实例／案例集
└── scripts/
    ├── pipeline/                   # 转写与配图（流水线第 1 步）
    ├── book/                       # 课程音视频成书（含版式 v2、再分段 v3）
    ├── book8/                      # 本地资料成书（含 OCR、体系抽离）
    └── book9/                      # 案例集（素材分诊与分卷）
```

`SKILL.md` 里为保持原项目习惯使用了 `$T/book/xxx.py` 这类写法，**仓库路径对照表在 SKILL.md 顶部**。

**`references/` 三份是模板，不是成品**：开工时复制一份进你的项目（如 `<项目根>/book/STYLE_GUIDE.md`），把占位符换成你的课程信息，再逐课追加错字表与专用说明。子代理整理每一节时都会完整读它——它是质量的总闸门。

---

## 安装

把整个仓库放进 skill 目录：

```bash
git clone <你的仓库地址> ~/.workbuddy/skills/lecture-materials-to-book
```

（Claude Code / 其他支持 Agent Skill 的客户端同理，放进其 skills 目录即可。）

---

## 环境依赖

- **Windows + 安装有 Microsoft Word**：页码目录（TOC 域）的更新与 PDF 导出走 Word COM，这是唯一没有替代方案的一环。
- **Python 3.11+**（实测 3.13）
- 包：
  - 排版与文档：`python-docx`、`pywin32`
  - 阅读与校验：`pymupdf`、`Pillow`
  - 转写：`faster-whisper`（可选，配 CUDA 更快）
  - 扫描件 OCR：`rapidocr-onnxruntime`
  - 音视频处理：`av`、`numpy`

脚本一律用 `__file__` 相对定位，**不依赖绝对路径**。项目特有的书单／课程名／前缀写在脚本顶部常量里（`ALL_BOOKS`、`BOOKS`、`LECTURER`、`RENAME` 等），换项目时改这几处。

---

## 快速开始

```bash
# ── 第 1 步：转写（音视频 → 文字稿）
python scripts/pipeline/run_transcribe.py --course 01

# ── 第 2 步：分节整理（派子代理逐节整理，见 SKILL.md 第一节）——
#    每节输出 sec-md/<前缀>-NNN.md，首行 ## 节标题，纯文本、无列表无加粗

# ── 第 3 步：引号统一（必做前置！否则引文提行规则失效）
python scripts/book/normalize_quotes.py --dry    # 先查奇数配对
python scripts/book/normalize_quotes.py

# ── 第 4 步：正文再分段（规则层）
python scripts/book/reparagraph.py --dry
python scripts/book/reparagraph.py

# ── 第 5 步：AI 复核（语义临界长段 / 孤立碎句）
python scripts/book/ai_candidates.py             # 生成待复核清单 → 交给子代理
python scripts/book/ai_apply.py --dry            # 先试算
python scripts/book/ai_apply.py                  # 落地（逐字符校验）

# ── 第 6 步：排版成书籍版式
python scripts/book/format_books.py

# ── 第 7 步：更新目录页码并导出 PDF
python scripts/book/update_toc.py
```

最后务必做**收尾四件事**：QA 三扫 → 页数核对 → 抽页渲染肉眼确认（封面／扉页／引文块／目录页码）→ 更新技能与记忆。

---

## 默认规范（摘要，完整版见 SKILL.md 第〇节）

1. **正文纯文本**：无列表、无加粗、**无斜体**；标题不带书名。
2. **一律正体**：Word 内置的 Heading 4/6/7/9、Subtitle、Quote、Emphasis 等 **17 个样式自带斜体**，必须显式关掉，否则「（一）」这一级目会整级变斜体。存量文档用 `strip_italic.py` 批量清。
3. **版式 v2**：编/卷=H1、章/节=H2、小节「一、」=H3、目「（一）」=H4；封面书名不占 Heading 样式；目录域只收 1–2 级；正文行距 1.5／段后 3pt。
4. **再分段／提行 v3**：先统一引号 → 规则层 → AI 复核层。**只动换行，一个字都不改**，逐字符硬校验。
5. **内容规范**：零品牌／零真实人名关联；标志性方法论整章抽出另成册；不评价当代政治人物。
6. **交付**：`docx` + `pdf` + `md` 三件齐全；批量重排前先把旧 docx 备份到 `_old_docx/`（否则做不出真实前后对照图）。
7. **收尾四件事**：QA 三扫、页数核对、抽页肉眼确认、更新记忆与技能。

---

## 脚本清单

### `scripts/pipeline/` — 转写与配图

| 脚本 | 作用 |
|---|---|
| `run_transcribe.py` | 批量转写音视频（faster-whisper，断点续跑，20 分钟切片逐片落盘） |
| `audio_utils.py` | 音频切片、重采样 |
| `cuda_env.py` | CUDA DLL 路径配置（让 faster-whisper 走 GPU） |
| `bench_speed.py` / `probe_duration.py` | 转写速度基准 / 音视频时长探测 |
| `batch_scene_frames.py` | 批量场景抽帧驱动（python 循环，避开中文文件名） |
| `grab_frames.py` / `scene_frames.py` | 按时间点抓帧 / 按场景变化抓帧（配图素材） |
| `insert_figures.py` / `build_album.py` | 配图插入 docx / 生成图册 docx |
| `volume_check.py` | 音量与电平静音检测（排查"转写稿明显偏短"） |

### `scripts/book/` — 课程音视频成书

| 脚本 | 作用 |
|---|---|
| `reparagraph.py` | **正文再分段引擎 v3**：长段装箱切分、引文提行、韵文逐句成行、并列项裂开 |
| `normalize_quotes.py` | **引号统一**：半角 `"` → `“”`（分段前必跑） |
| `ai_candidates.py` / `ai_apply.py` | AI 复核层的候选清单生成 / 结果落地（零改字硬校验） |
| `format_books.py` | **版式 v2 批量排版**（四级标题、TOC 域、图注样式） |
| `update_toc.py` | 用 Word COM 更新目录页码 → 保存 → 导出 PDF |
| `strip_italic.py` | **清除斜体**（按 part 比对，超出预期即放弃写入） |
| `split_scripture.py` | 参照原文按节切分（逐句讲解课用） |
| `merge_book*.py` / `insert_book*.py` | 各书合并与插入 docx（6+6 个，作为模板参考） |
| `format_bookYT.py` | 单本定制版式示例 |
| `check_pages.py` / `check_pages_all.py` | 页数与大纲核对 |

### `scripts/book8/` — 本地资料成书（讲义 + 扫描件）

| 脚本 | 作用 |
|---|---|
| `extract_materials.py` | 从讲义 PDF/docx 批量提取文字 |
| `ocr_batch.py` / `test_ocr.py` | 扫描件 OCR（RapidOCR），含效果与速度测试 |
| `format_book8.py` | 版式 v2（本地资料版，`LECTURER` 留空则封面只署整理者） |
| `reparagraph.py` | 再分段引擎（按章处理版，与 `book/` 同源） |
| `merge_bookBZ.py` | 汇编成书（编/章三级骨架） |
| `build_companion.py` | **姊妹册汇编示例**：从备份稿回捞整段，另成一册 |
| `strip_brand_extract.py` | **去品牌化 + 体系抽离示例**（改中性词、整章抽出） |
| `strip_season.py` | 按内容框架抽章／抽节示例（可重入，含编号重排） |
| `update_toc.py` / `check_all.py` / `check_pages_all.py` | 收尾校验与导出 |

### `scripts/book9/` — 案例集

| 脚本 | 作用 |
|---|---|
| `extract_cases.py` | 从 OCR 素材抽取实例 |
| `census.py` / `triage.py` | 素材盘点与分级（去重、按质量排序） |
| `clean_brand.py` | 素材层去品牌清理（放在子代理之前，防照抄） |
| `build_volumes.py` | 分卷汇编 |

---

## 三条硬口径（做完必须自己验一遍）

1. **零改字**：分段／提行只允许增删空白与 `> ` 前缀。校验方式＝去掉空白与 `> ` 后**逐字符比对**，不一致就回滚。
2. **一律正体**：`pymupdf` 遍历 PDF 全部 span，`flags & 2`（斜体位）必须为 **0**；docx 里 `grep '<w:i/>'` 必须为 0。
3. **内容干净**：品牌名与人名的残留计数必须为 0（交付前 `grep -c` 核）。

---

## 已知坑（详见 SKILL.md 第三节）

- `reparagraph.py` 的引文提行只认 `“…”`，**半角引号没统一就等于白做**——这是最常见的返工原因。
- python-docx 写成标题时用的是 `w:outlineLvl`，而 python-docx 自己生成的看 `p.style.name`，两套读法不一样。
- 分卷书的三级标题必须让分块函数支持 `### `，否则 docx 丢三级大纲。
- 并列项切分的正则别写太宽：`(?=其[一二三])` 会把「。**其实**……」「。**第一句**……」误判成条目。
- 引文块末尾紧跟的句号要并回引文行，否则会出现只含一个「。」的孤段。

---

## 说明

本仓库为**通用版**：

- 与具体领域无关：文中出现的课程名、书名、卷名均为**结构示范**，不指向任何具体作品；
- 路径一律写作占位符（`<项目根>`、`<转写源目录>`、`<媒体盘>`、`<资料目录>`、`<venv>`），使用时替换为自己的实际目录；
- 人名、品牌名、机构名统一用 `【品牌名】`、`【讲授者】`、`【机构名】` 占位；
- 不含任何具体项目的课程清单与进度记录；文中的页数、字数、段落数等统计是真实的量级，可作参数参考；
- 脚本顶部常量（`ALL_BOOKS`、`BOOKS`、`LECTURER`、`VOLUMES`、`RENAME` 等）里的书名与替换表均为占位示例，按自己的项目改写即可。
