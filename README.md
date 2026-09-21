# GitHub Graffiti 🎨

在 GitHub 主页贡献热力图（Contribution Graph）上拼出你想要的单词！

利用回溯日期的 git 提交，把一年 52 周 × 7 天的热力图当作 7 像素高的点阵屏，
拼出 `LOVE`、`HELLO`、`HI`、`2026` …… 让你的 GitHub 主页与众不同。

```
Sun  │                  L    O    V    E
Mon  │                  L    O    V    E
Tue  │                  L    O    V    E
Wed  │                  L    O    V   ####
Thu  │                  L    O    V    E
Fri  │                  L    O   V.V   E
Sat  │               ##### .###. ..#.. #####
```

## 特性

- ✅ 自定义单词（26 字母 + 10 数字 + `! ? . , : ' - _ / = # + * < > ( ) [ ]` 等符号，`@` 是爱心 ❤）
- ✅ `--preview` 纯本地预览，先看效果再决定提交
- ✅ `--show-font` 打印内置字库
- ✅ `--commits-per-pixel` 控制颜色深浅（活跃账号可调到 10+）
- ✅ `--real-files` 提交真实 HTML 文件而非空提交，更"像真的"
- ✅ `--stealth` 防封模式：时间戳/提交信息/改动量随机化 + 分批推送
- ✅ `--erase` 擦除旧单词，干净换词不叠影（只动涂鸦提交，正常提交原样保留）
- ✅ GitHub Actions 一键换词（擦旧词 + 画新词一次运行完成）
- ✅ 自动检查提交邮箱是否绑定 GitHub 账号
- ✅ 单文件 Python 脚本，零依赖；测试也只用标准库

## 快速开始

```bash
# 1. 预览效果（不产生任何提交）
python3 graffiti.py --word LOVE --preview

# 2. 生成提交到本地 ./repo 目录
python3 graffiti.py --word LOVE --commits-per-pixel 4

# 3. 生成并推送到你的仓库
python3 graffiti.py --word LOVE \
    --remote git@github.com:you/your-repo.git \
    --push
```

不想敲命令？直接用 [GitHub Actions 一键换词](#github-actions-一键换词)。

## GitHub Actions 一键换词

仓库自带 [.github/workflows/graffiti.yml](.github/workflows/graffiti.yml)，
在 Actions 页面填个单词点 Run，自动完成「擦旧词 + 画新词 + 强推」：

1. 创建 PAT：Settings → Developer settings → Personal access tokens
   （Classic 勾选 `repo`，或 Fine-grained 给目标仓库 Contents 读写权限）
2. 添加仓库 Secret：本仓库 Settings → Secrets and variables → Actions →
   新建 `GRAFFITI_PAT`，值为上面的 token
3. 本仓库 Actions → Graffiti → Run workflow，填写：
   - `word`：新单词（留空 = 只擦除）
   - `erase_word`：要擦除的旧单词（留空 = 不擦除）
   - `commits_per_pixel` / `weeks_ago` / `target_repo`：可选

> 为什么需要 PAT：Actions 默认 `GITHUB_TOKEN` 推的提交**不一定计入贡献图**
> （github-actions bot 相关提交会被排除），用自己的 PAT 推送 + noreply 邮箱
> 才能保证计入。workflow 会自动用 `<actor_id>+<actor>@users.noreply.github.com`
> 作为提交邮箱。

## 参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `--word` | (必填) | 要显示的单词，最多约 8 个字符（52 列限制） |
| `--repo` | `./repo` | 本地仓库路径，不存在则自动 init |
| `--remote` | - | 远程仓库地址 |
| `--push` | - | 生成后自动推送 |
| `--weeks-ago` | `1` | 单词**最后一列**距当前周往回几周 |
| `--commits-per-pixel` | `4` | 每个像素的提交数，越多颜色越深 |
| `--real-files` | - | 提交真实修改 `graffiti/<word>.html` 而非空提交 |
| `--stealth` | - | 防封模式（见下） |
| `--erase` | - | 擦除模式：删除已有涂鸦提交并重写历史（见下） |
| `--push-batch N` | `50` | 防封分批推送时每批的提交数 |
| `--seed N` | - | 固定随机种子，可复现结果 |
| `--preview` | - | 仅预览，不做任何提交 |
| `--show-font` | - | 打印内置字库后退出（不用给 `--word`） |

> `--weeks-ago` 数的是单词**最右边**那一列。宽度 5 的字母里只有中间一列
> 有点（比如 `!`），它会落在 `weeks-ago + 2` 周前的位置。

## 防封模式 (--stealth)

一次性推送几百个规律重复的提交容易被判定为机器人行为。加上 `--stealth` 后：

- **提交时间随机化**：同一天的多个提交随机落在 9:00–23:00 之间（乱序、带随机秒数），而不是等间隔网格
- **提交信息多样化**：从真实开发用语池随机抽取（`fix typo` / `wip` / `refactor xxx` …），不再千篇一律
- **文件改动量随机**：real-files 模式下每次追加 1~5 行随机内容
- **分批推送**：每批 `--push-batch`（默认 50）个提交，批间随机延时 3~8 秒，避免触发限流

```bash
python3 graffiti.py --word LOVE --real-files --stealth --commits-per-pixel 10 --push
```

## 覆盖旧单词 (--erase)

热力图格子显示的是**当日提交总数**，旧涂鸦的提交一直在历史里，直接画新词只会两个词叠在一起。
想干净地换词（比如用 `FADE` 覆盖 `LOVE`），必须先擦掉旧提交：

```bash
# 1. 擦除 LOVE (自动识别它的提交, 重写历史)
python3 graffiti.py --word LOVE --repo ./profile-repo --erase --push

# 2. 等 GitHub 重算热力图 (几分钟~24小时), 旧格子变灰后, 再画新词
python3 graffiti.py --word FADE --repo ./profile-repo --real-files --stealth --push
```

擦除怎么认出"哪些提交是这个词的"——两条线索取并集：

| 画法 | 留下的痕迹 |
|---|---|
| `--real-files` | 提交碰过 `graffiti/<word>.html` |
| 空提交（默认） | 提交信息形如 `graffiti: <WORD> [...]` |

⚠️ **`--stealth` + 空提交画的词认不出来**：那种提交信息是从开发用语池里随机抽的，
文件名也不存在。想以后能擦掉，就用 `--real-files`（`--stealth` 可以和它同时用）。

擦除只动属于这个单词的提交，其余提交原样保留：

- 涂鸦提交整段在分支末尾 → 直接 `reset`，快，更早的历史一个字节都不动
- 与正常提交交错 → `filter-branch` 逐个剔除，正常提交的**内容、作者、提交时间**都保留
  （父提交变了所以 sha 会变，这是重写历史的固有代价）
- ⚠️ force push 会重写远程历史，若有协作者请先沟通

## 字符集与自定义字形

内置 57 个字形（26 字母 + 10 数字 + 21 个符号，`@` 是爱心），用 `--show-font` 全部打印出来：

```bash
python3 graffiti.py --show-font
```

字形定义在 `graffiti.py` 顶部的 `FONT` 字典里，每个字符 7 行、每行 6 个字符：

```python
"L": [" #....", " #....", " #....", " #....", " #....", " #....", " #####"],
#     ↑左边距  └────── 真正的 5 列, # 亮 / . 暗 ──────┘
```

想加自己的图案（logo、方块、箭头…），照着格式往 `FONT` 里加一条就行，
字符之间的 1 列间隔是自动加的。`n` 个字符占 `6n-1` 列，超过 52 列会被一年窗口裁掉。

## 常见问题

**热力图没变化 / 格子不亮**

1. 提交邮箱必须绑在你的 GitHub 账号上（Settings → Emails）。脚本结束时会打印当前仓库的提交邮箱，对着看一眼。
2. 热力图是异步重算的，force push 之后要几分钟到 24 小时才更新。
3. 账号平时很活跃时，涂鸦的提交数盖不过背景——把 `--commits-per-pixel` 调大。

**`git commit` 报 "Please tell me who you are"**

脚本会在动手前拦下来并告诉你怎么配：

```bash
git -C ./repo config user.name  "你的用户名"
git -C ./repo config user.email "你的GitHub邮箱"
```

**Actions 里 push 报 `400 Duplicate header: Authorization`**

`actions/checkout` 带 `token` 时默认会把 token 写进 `.git/config` 的 `extraheader`，
和 workflow 自己配的那条叠成两个 `Authorization` 头。workflow 里已经用
`persist-credentials: false` 关掉了，如果你改过那段，记得保留。

**Actions 里 push 报 403 / 认证失败**

PAT 权限不够。Classic PAT 勾 `repo`；Fine-grained PAT 给目标仓库
**Contents: Read and write**。workflow 会先用 `git ls-remote` 验一次，失败会直接说清楚。

**空提交算不算贡献？**

算。GitHub 只要求"邮箱绑定在你账号上的提交存在于默认分支上"，不看改动量。
`--allow-empty` 的提交照样计一格。

## 开发

测试只用标准库，不需要装任何东西：

```bash
python3 -m unittest discover -s tests -v
```

45 个测试覆盖点阵渲染、列→周的日期映射、防封模式的随机化、`--erase` 的两条路径
（reset / filter-branch），以及 workflow 里几个踩过的坑（token 泄露、重复认证头）。
测试都在临时目录里建自己的 git 仓库，不会碰 `./repo` 和 `./profile-repo`。

## 颜色深浅怎么调？

GitHub 热力图按**当日提交总数**分档（Less → More 共 5 档）。你的账号平时活跃度越高，
涂鸦要盖过背景需要的提交数就越多：

| 情况 | 建议值 |
|---|---|
| 账号基本空白 | 1–2 |
| 普通账号 | 4–8 |
| 非常活跃（或想保证满格深绿） | 10+ |

同一天的多个提交时间戳会自动铺满全天，互不重叠。

## 原理

GitHub 主页的贡献热力图是 **7 行（周日→周六）× 52 列（周）** 的网格，恰好是一块
7 像素高的点阵屏。每个字母用 5×7 点阵渲染，占 5 列 + 1 列间隔；脚本用
`GIT_AUTHOR_DATE` / `GIT_COMMITTER_DATE` 把每个 `--allow-empty`（或真实文件改动）
的提交回溯到对应日期，推送后对应格子就亮了。

贡献图的计算规则（也是 `--erase` 能生效的原因）：按**当前默认分支上实际存在的提交**
统计，邮箱须绑定在你账号上。所以删掉涂鸦提交并 force push 后，GitHub 重算时旧格子
会清空。

## 注意事项

1. **提交邮箱必须绑定在你的 GitHub 账号上**（Settings → Emails），否则热力图不计数。
   脚本结束时自动打印当前仓库的提交邮箱供检查。
2. 建议先在 GitHub 新建一个空仓库（不勾选 README），再把地址传给 `--remote`。
3. 推送到已有人协作的仓库请谨慎——232 个涂鸦提交会刷满协作者的 timeline。
4. 单词太长（>8 字符）会超出一年窗口，可减小 `--weeks-ago` 或缩短单词。

## 更多玩法

- 爱心：`--word "I@YOU"` ❤
- 年份：`--word 2026`
- 方块和符号：`--word "[#_#]"`、`--word "A=B"`、`--word "1+1"`
- 一句短语（注意 8 字符上限）：`--word "HI YOU"`

想玩点字库没有的，照「字符集与自定义字形」自己加图案即可。

## License

MIT
