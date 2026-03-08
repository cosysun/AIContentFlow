# 小红书内容生成 SOP（文字 + 图片）

> 最后更新：2026-03-08  
> 适用场景：将原始文章/访谈素材，生成小红书正文 + 8 张配图

---

## 一、两种模式对比

| 模式 | 步骤 | 适用场景 |
|------|------|----------|
| **手动模式**（当前） | 我生成 prompts → 上传 Notion → 你去 nano banana pro 出图 | 需要人工审核 prompt、调整风格 |
| **自动模式**（待配置） | 一条命令 → 自动出图到本地 | 批量生产、无需干预 |

---

## 二、手动模式 SOP（当前标准流程）

### 前置条件
- 文章已写好，存放在 `/data/workspace/.draft/YYYY-MM-DD/` 目录
- 文章为小红书版本（已经过平台适配）

### Step 1：生成 prompts.md

告诉我：

> 「帮我为 [文章名] 生成小红书图片 prompts」

我会：
1. 读取文章内容
2. 按 **8张图结构** 生成 prompts（见下方规范）
3. 保存到 `AIContentFlow/outputs/archive/YYYY-MM-DD/文章名_小红书图片prompts.md`

### Step 2：上传到 Notion

告诉我：

> 「上传到 Notion」

我会自动调用 `notion_publisher.py`，将 prompts.md 上传到 Notion 草稿箱，并返回链接。

### Step 3：在 nano banana pro 出图

1. 打开 Notion 链接
2. 找到 **图01_封面** 的 prompt，复制给 nano banana pro
3. 图01 生成后，**图02-08 生成时带上 `--ref 图01.png`**，保持风格统一
4. 所有图片下载到本地

### Step 4：发布小红书

- 封面 = 图01
- 正文 = 文章小红书版
- 图片顺序：图01 → 图08

---

## 三、文字正文规范

> 核心原则：**文字只留情绪和互动，内容交给图片说**  
> 小红书用户浏览路径：封面图 → 滑动看图 → 最后才看文字，图片是主角

### 字数与结构

| 项目 | 规范 |
|------|------|
| **字数** | 150–250 字 |
| **语言** | 口语化，多用 emoji |
| **结构** | Hook（1-2句）→ 核心感受/发现（2-4句）→ 互动引导（1句） |
| **标签** | 5-8 个话题标签 |

### 保留 vs 删除

| ✅ 保留 | ❌ 删掉 |
|---------|---------|
| 制造悬念/共鸣的开场句 | 背景铺垫、来龙去脉 |
| 最打动人的 1-2 个金句（不解释，只陈述） | 逻辑推导过程 |
| 互动引导结尾 | 总结归纳、观点解释 |

### 写作风格

- 具体事实代替抽象描述（如「发布3天登上 GitHub Trending」而非「引起广泛关注」）
- 主动语态，短句为主
- 减少过渡词，直接说事实
- 适当提问与读者互动

### 正文模板

```
[Hook：1-2句，制造悬念或强烈共鸣]

[核心感受/发现：2-4句，不解释，只陈述最打动人的事实/金句]

[互动引导：1句，引发评论或收藏]

#话题标签1 #话题标签2 #话题标签3 ...
```

---

## 四、8张图结构规范

| 编号 | 用途 | 布局 | 要点 |
|------|------|------|------|
| 图01 | **封面** | Sparse | 强冲击力标题 + 悬念感，极简留白 |
| 图02 | 人物/背景介绍 | Balanced | 谁做了什么，关键数字 |
| 图03 | 核心观点1 | Comparison/List | 文章最重要的论点 |
| 图04 | 核心观点2 | List/Dense | 第二个重要论点 |
| 图05 | 核心观点3 | Flow/Dense | 第三个重要论点 |
| 图06 | 金句/深度思考 | Sparse/Quote | 最有共鸣的一句话 |
| 图07 | 总结/启示 | Balanced/List | 读者能带走什么 |
| 图08 | 结尾互动 | Sparse | 引发思考的问题 + 评论引导 |

---

## 五、Prompt 风格规范（Notion 手绘风）

每个 prompt 固定结构：

```
Create a Xiaohongshu (Little Red Book) style infographic following these guidelines:

**Image Specifications**: Portrait 3:4, Hand-drawn illustration style, ALL text in Chinese

**Core Principles**:
- Hand-drawn quality throughout - NO realistic or photographic elements
- Keep information concise, highlight keywords and core concepts
- Use ample whitespace for easy visual scanning
- Maintain clear visual hierarchy

**Text Style**: ALL text MUST be hand-drawn style, main titles prominent, use highlighter effects on keywords

**Style**: Notion — Black (#1A1A1A)/white (#FFFFFF) base, pastel blue (#A8D4F0)/yellow (#F9E79F)/pink (#FADBD8) accents, simple line doodles, maximum whitespace, single-weight ink lines

**Layout**: [Sparse/Balanced/Comparison/List/Flow/Dense]

**Content**:
[中文内容：标题、要点、金句、互动引导等]

**Visual Concept**:
[具体的画面描述：人物、图标、构图、颜色分布等]

Please use nano banana pro to generate the infographic based on the specifications above.
```

> ⚠️ Content 部分用中文（图片里显示的文字）  
> ⚠️ 描述性部分（Style/Layout/Visual Concept）用英文

---

## 六、自动模式（待配置）

### 配置方式

在 `/data/workspace/AIContentFlow/.env` 中添加：

```
GRSAI_API_KEY=你的GrsAI密钥
ANTHROPIC_API_KEY=你的Claude密钥
```

### 运行命令

```bash
python3 /data/workspace/AIContentFlow/tools/xhs_image_pipeline.py \
  /data/workspace/.draft/YYYY-MM-DD/文章名_小红书版.md
```

### 输出结果

```
.draft/YYYY-MM-DD/文章名_小红书版_images/
├── 文章名_image_prompts.md   # prompts 备份
├── 01_图01_封面.png
├── 02_图02_人物背景.png
├── ...
├── 08_图08_结尾互动.png
└── report.json               # 生成报告
```

---

## 七、相关文件索引

| 文件 | 用途 |
|------|------|
| `tools/xhs_image_pipeline.py` | 自动模式主脚本 |
| `publisher/notion_publisher.py` | 上传 Notion 脚本 |
| `outputs/archive/YYYY-MM-DD/` | 历史 prompts 归档 |
| `.env` | API 密钥（不上传 Git） |

---

## 八、完整流程一览

```
给 Knot 提供原始文章/素材
    ↓
Step 1：生成小红书正文（150-250字）
    ↓
Step 2：生成图片 prompts.md（8张图）
    ↓
Step 3：上传 Notion → 返回草稿链接
    ↓
Step 4：打开 Notion，复制 prompt 给 nano banana pro
    ↓
图01 先出，图02-08 带 --ref 图01.png
    ↓
下载图片 → 配小红书正文 → 发布 ✅
```
