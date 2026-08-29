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

- ✅ 自定义单词（A–Z、0–9、空格、`! ? . - + * < >`，`@` 是爱心 ❤）
- ✅ `--preview` 纯本地预览，先看效果再决定提交
- ✅ `--commits-per-pixel` 控制颜色深浅（活跃账号可调到 10+）
- ✅ `--real-files` 提交真实 HTML 文件而非空提交，更"像真的"
- ✅ 自动检查提交邮箱是否绑定 GitHub 账号
- ✅ 单文件 Python 脚本，零依赖

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

## 参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `--word` | (必填) | 要显示的单词，最多约 8 个字符（52 列限制） |
| `--repo` | `./repo` | 本地仓库路径，不存在则自动 init |
| `--remote` | - | 远程仓库地址 |
| `--push` | - | 生成后自动推送 |
| `--weeks-ago` | `1` | 单词最后一列距当前周往回几周 |
| `--commits-per-pixel` | `4` | 每个像素的提交数，越多颜色越深 |
| `--real-files` | - | 提交真实修改 `graffiti/<word>.html` 而非空提交 |
| `--stealth` | - | 防封模式（见下） |
| `--push-batch N` | `50` | 防封分批推送时每批的提交数 |
| `--seed N` | - | 固定随机种子，可复现结果 |
| `--preview` | - | 仅预览，不做任何提交 |

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
# 1. 擦除 LOVE (自动识别 graffiti/love.html 的提交, 重写历史)
python3 graffiti.py --word LOVE --repo ./profile-repo --erase --push

# 2. 等 GitHub 重算热力图 (几分钟~24小时), 旧格子变灰后, 再画新词
python3 graffiti.py --word FADE --repo ./profile-repo --real-files --stealth --push
```

- 贡献图按**当前分支上实际存在的提交**计算，force push 移除后旧格子会清空
- 涂鸦提交全在尾部时直接 reset（快）；与正常提交交错时用 filter-branch 逐个剔除（正常提交保留）
- ⚠️ force push 会重写远程历史，若有协作者请先沟通

## 颜色深浅怎么调？

GitHub 热力图按**当日提交总数**分档（Less → More 共 5 档）。你的账号平时活跃度越高，
涂鸦要盖过背景需要的提交数就越多：

| 情况 | 建议值 |
|---|---|
| 账号基本空白 | 1–2 |
| 普通账号 | 4–8 |
| 非常活跃（或想保证满格深绿） | 10+ |

同一天的多个提交时间戳会自动铺满全天，互不重叠。

## ⚠️ 注意事项

1. **提交邮箱必须绑定在你的 GitHub 账号上**（Settings → Emails），否则热力图不计数。
   脚本结束时自动打印当前仓库的提交邮箱供检查。
2. 建议先在 GitHub 新建一个空仓库（不勾选 README），再把地址传给 `--remote`。
3. 推送到已有人协作的仓库请谨慎——232 个涂鸦提交会刷满协作者的 timeline。
4. 单词太长（>8 字符）会超出一年窗口，可减小 `--weeks-ago` 或缩短单词。

## 已知样式

- 用 `@` 当爱心：`--word "I@YOU"` ❤

## License

MIT
