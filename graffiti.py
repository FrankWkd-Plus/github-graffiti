#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 热力图涂鸦 (Contribution Graph Graffiti)

用回溯日期的空提交，在 GitHub 主页贡献热力图上拼出自定义单词。
热力图: 7 行(周日~周六) x ~53 列(周)，正好当作 7 像素高的点阵屏，
每个字母占 5 列宽 + 1 列间隔。

用法示例:
  # 预览效果(不提交)
  python3 graffiti.py --word HELLO --preview

  # 生成提交(本地仓库 ./repo)
  python3 graffiti.py --word HELLO

  # 生成并推送到已有远程仓库
  python3 graffiti.py --word HELLO --remote git@github.com:you/your-repo.git --push

  # 每个像素点 3 个提交(颜色更深)、结束位置往前推 4 周
  python3 graffiti.py --word 2026 --commits-per-pixel 3 --weeks-ago 4
"""

import argparse
import os
import random
import subprocess
import sys
import time
from datetime import date, timedelta

# ---------------- 5x7 点阵字体 ----------------
# 每个字符: 7 行, 每行 5 个字符, '#' 为点亮像素
FONT = {
    "A": [" .###.", " #...#", " #...#", " #####", " #...#", " #...#", " #...#"],
    "B": [" ####.", " #...#", " #...#", " ####.", " #...#", " #...#", " ####."],
    "C": [" .###.", " #...#", " #....", " #....", " #....", " #...#", " .###."],
    "D": [" ####.", " #...#", " #...#", " #...#", " #...#", " #...#", " ####."],
    "E": [" #####", " #....", " #....", " ####.", " #....", " #....", " #####"],
    "F": [" #####", " #....", " #....", " ####.", " #....", " #....", " #...."],
    "G": [" .###.", " #...#", " #....", " #.###", " #...#", " #...#", " .###."],
    "H": [" #...#", " #...#", " #...#", " #####", " #...#", " #...#", " #...#"],
    "I": [" #####", " ..#..", " ..#..", " ..#..", " ..#..", " ..#..", " #####"],
    "J": [" ..###", " ...#.", " ...#.", " ...#.", " ...#.", " #..#.", " .##.."],
    "K": [" #...#", " #..#.", " #.#..", " ##...", " #.#..", " #..#.", " #...#"],
    "L": [" #....", " #....", " #....", " #....", " #....", " #....", " #####"],
    "M": [" #...#", " ##.##", " #.#.#", " #...#", " #...#", " #...#", " #...#"],
    "N": [" #...#", " ##..#", " #.#.#", " #..##", " #...#", " #...#", " #...#"],
    "O": [" .###.", " #...#", " #...#", " #...#", " #...#", " #...#", " .###."],
    "P": [" ####.", " #...#", " #...#", " ####.", " #....", " #....", " #...."],
    "Q": [" .###.", " #...#", " #...#", " #...#", " #.#.#", " #..#.", " .##.#"],
    "R": [" ####.", " #...#", " #...#", " ####.", " #.#..", " #..#.", " #...#"],
    "S": [" .####", " #....", " #....", " .###.", " ....#", " ....#", " ####."],
    "T": [" #####", " ..#..", " ..#..", " ..#..", " ..#..", " ..#..", " ..#.."],
    "U": [" #...#", " #...#", " #...#", " #...#", " #...#", " #...#", " .###."],
    "V": [" #...#", " #...#", " #...#", " #...#", " #...#", " .#.#.", " ..#.."],
    "W": [" #...#", " #...#", " #...#", " #...#", " #.#.#", " ##.##", " #...#"],
    "X": [" #...#", " #...#", " .#.#.", " ..#..", " .#.#.", " #...#", " #...#"],
    "Y": [" #...#", " #...#", " .#.#.", " ..#..", " ..#..", " ..#..", " ..#.."],
    "Z": [" #####", " ....#", " ...#.", " ..#..", " .#...", " #....", " #####"],
    "0": [" .###.", " #...#", " #..##", " #.#.#", " ##..#", " #...#", " .###."],
    "1": [" ..#..", " .##..", " ..#..", " ..#..", " ..#..", " ..#..", " #####"],
    "2": [" .###.", " #...#", " ....#", " ...#.", " ..#..", " .#...", " #####"],
    "3": [" .###.", " #...#", " ....#", " ..##.", " ....#", " #...#", " .###."],
    "4": [" ...#.", " ..##.", " .#.#.", " #..#.", " #####", " ...#.", " ...#."],
    "5": [" #####", " #....", " ####.", " ....#", " ....#", " #...#", " .###."],
    "6": [" .###.", " #....", " #....", " ####.", " #...#", " #...#", " .###."],
    "7": [" #####", " ....#", " ...#.", " ..#..", " .#...", " .#...", " .#..."],
    "8": [" .###.", " #...#", " #...#", " .###.", " #...#", " #...#", " .###."],
    "9": [" .###.", " #...#", " #...#", " .####", " ....#", " ....#", " .###."],
    " ": [" .....", " .....", " .....", " .....", " .....", " .....", " ....."],
    "!": [" ..#..", " ..#..", " ..#..", " ..#..", " ..#..", " .....", " ..#.."],
    "?": [" .###.", " #...#", " ....#", " ...#.", " ..#..", " .....", " ..#.."],
    ".": [" .....", " .....", " .....", " .....", " .....", " .....", " ..#.."],
    "-": [" .....", " .....", " .....", " #####", " .....", " .....", " ....."],
    "+": [" .....", " ..#..", " ..#..", " #####", " ..#..", " ..#..", " ....."],
    "*": [" .....", " #.#.#", " ..#..", " #####", " ..#..", " #.#.#", " ....."],
    "<": [" ...#.", " ..#..", " .#...", " #....", " .#...", " ..#..", " ...#."],
    ">": [" .#...", " ..#..", " ...#.", " ....#", " ...#.", " ..#..", " .#..."],
    # 爱心
    "@": [" .#.#.", " #####", " #####", " #####", " .###.", " ..#..", " ....."],
}

ROW_LABELS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

# 真实开发风格的提交信息池 (防封: 避免所有 message 一个模板)
COMMIT_MSG_POOL = [
    "update {file}",
    "fix bug in {file}",
    "refactor {file}",
    "tweak {file}",
    "cleanup {file}",
    "polish {file}",
    "adjust styles in {file}",
    "minor fix",
    "wip",
    "update docs",
    "fix typo",
    "improve readability",
    "small refactor",
    "code cleanup",
    "adjust layout",
    "tweak colors",
    "update comment",
    "lint fixes",
    "format code",
    "sync changes",
]


def render_word(word):
    """把单词渲染成 7 行的像素矩阵 (list of str, '#'=点亮)"""
    word = word.upper()
    rows = ["", "", "", "", "", "", ""]
    for i, ch in enumerate(word):
        if ch not in FONT:
            sys.exit(f"错误: 不支持的字符 '{ch}' (支持 A-Z 0-9 空格 !?.-+*<> 和 @ 代表爱心)")
        glyph = FONT[ch]
        for r in range(7):
            rows[r] += glyph[r][1:] + (" " if i < len(word) - 1 else "")
    return rows


def git(repo, *args, env=None, check=True):
    """执行 git 命令"""
    cmd = ["git", "-C", repo] + list(args)
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if check and result.returncode != 0:
        sys.exit(f"git 命令失败: {' '.join(cmd)}\n{result.stderr}")
    return result


def main():
    parser = argparse.ArgumentParser(description="在 GitHub 热力图上拼出自定义单词")
    parser.add_argument("--word", required=True, help="要显示的单词 (A-Z 0-9 空格 等)")
    parser.add_argument("--repo", default="./repo", help="本地仓库路径 (默认 ./repo, 不存在则自动 init)")
    parser.add_argument("--remote", help="远程仓库地址 (如 git@github.com:you/your-repo.git)")
    parser.add_argument("--push", action="store_true", help="生成后推送到远程")
    parser.add_argument("--weeks-ago", type=int, default=1,
                        help="单词最后一列距当前周往回几周 (默认 1, 避开当前周)")
    parser.add_argument("--commits-per-pixel", type=int, default=4,
                        help="每个像素的提交数, 越多颜色越深 (默认 4; "
                             "活跃账号可能需要 10 甚至更多才能明显显示)")
    parser.add_argument("--preview", action="store_true", help="仅预览, 不做任何提交")
    parser.add_argument("--real-files", action="store_true",
                        help="不用空提交, 每次提交真实修改 graffiti/<word>.html 文件")
    parser.add_argument("--stealth", action="store_true",
                        help="防封模式: 提交信息从真实开发用语池随机抽取, "
                             "时间戳随机化, 分批推送并带随机延时")
    parser.add_argument("--erase", action="store_true",
                        help="擦除模式: 删除已有涂鸦提交并重写历史 (需配合 --push 强推), "
                             "GitHub 重算热力图后旧格子清空, 即可用新单词覆盖")
    parser.add_argument("--push-batch", type=int, default=50,
                        help="分批推送每批的提交数 (默认 50, 配合 --stealth)")
    parser.add_argument("--seed", type=int, help="随机种子 (复现实验结果用)")
    args = parser.parse_args()

    rows = render_word(args.word)
    width = len(rows[0])

    # 热力图列(周)的计算: 当前的周(以周日为一周起点)
    today = date.today()
    current_week_start = today - timedelta(days=(today.weekday() + 1) % 7)  # 本周的周日
    # 单词最后一列所在周
    last_col_week_start = current_week_start - timedelta(weeks=args.weeks_ago)
    first_col_week_start = last_col_week_start - timedelta(weeks=width - 1)

    # 检查是否超出一年窗口
    one_year_ago = today - timedelta(days=365)
    if first_col_week_start < one_year_ago:
        print(f"警告: 单词起始列 ({first_col_week_start}) 超出了一年前 ({one_year_ago}), "
              f"超出的部分不会显示在主页热力图上。可缩短单词或减小 --weeks-ago。")

    # ---------------- 预览 ----------------
    total_weeks = 52
    grid_start = current_week_start - timedelta(weeks=total_weeks - 1)
    offset_weeks = (first_col_week_start - grid_start).days // 7

    print(f"\n单词: {args.word}  (宽 {width} 列, 结束于 {args.weeks_ago} 周前)\n")
    print("热力图预览 (最近一年, 右侧为本周):")
    print("      " + "┌" + "─" * total_weeks + "┐")
    for r in range(7):
        line = [" "] * total_weeks
        for c, ch in enumerate(rows[r]):
            if 0 <= offset_weeks + c < total_weeks:
                line[offset_weeks + c] = ch
        print(f"{ROW_LABELS[r]}  │" + "".join(line) + "│")
    print("      " + "└" + "─" * total_weeks + "┘\n")

    if args.preview:
        return

    # ---------------- 收集像素点 ----------------
    pixels = []  # (date, row, col)
    for c in range(width):
        week_start = first_col_week_start + timedelta(weeks=c)
        for r in range(7):
            if rows[r][c] == "#":
                pixels.append((week_start + timedelta(days=r), r, c))

    if not pixels:
        sys.exit("没有可提交的像素点 (单词是空的?)")

    print(f"共 {len(pixels)} 个像素点, 每点 {args.commits_per_pixel} 个提交, "
          f"合计 {len(pixels) * args.commits_per_pixel} 个提交")
    print(f"日期范围: {min(p[0] for p in pixels)} ~ {max(p[0] for p in pixels)}")

    # ---------------- 准备仓库 ----------------
    repo = os.path.abspath(args.repo)
    if not os.path.exists(repo):
        os.makedirs(repo)
    if not os.path.exists(os.path.join(repo, ".git")):
        git(repo, "init", "-b", "main")
        print(f"已初始化仓库: {repo}")

    if args.remote:
        r = git(repo, "remote", check=False)
        if "origin" in r.stdout.split():
            git(repo, "remote", "set-url", "origin", args.remote)
        else:
            git(repo, "remote", "add", "origin", args.remote)
        print(f"远程已设置: {args.remote}")

    # ---------------- 擦除模式 ----------------
    if args.erase:
        branch = git(repo, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        target = f"graffiti/{args.word.strip().lower().replace(' ', '_') or 'graffiti'}.html"
        before = int(git(repo, "rev-list", "--count", "HEAD").stdout.strip())

        # 所有碰过目标文件的提交
        glog = git(repo, "log", "--format=%H", "--", target).stdout.split()
        if not glog:
            print(f"没有找到与 {target} 相关的提交, 无需擦除。")
            return
        first = glog[-1]  # 最早的涂鸦提交

        # 所有碰过 graffiti/ 的提交集合
        graffiti_all = set(git(repo, "log", "--format=%H", "--", "graffiti").stdout.split())
        # first 的父提交 (若涂鸦提交是根提交则无父提交)
        rp = git(repo, "rev-parse", f"{first}^", check=False)
        tail_commits = set(git(repo, "rev-list", "HEAD").stdout.split()) \
            if rp.returncode != 0 else \
            set(git(repo, "rev-list", f"{rp.stdout.strip()}..HEAD").stdout.split())

        if rp.returncode == 0 and tail_commits <= graffiti_all:
            # 情况1: 涂鸦提交全部位于分支尾部, 直接 reset 到涂鸦开始前
            git(repo, "reset", "--hard", rp.stdout.strip())
            print("涂鸦提交位于分支尾部, 已 reset。")
        elif rp.returncode != 0 and tail_commits <= graffiti_all:
            # 边界: 整个仓库只有涂鸦提交, 无法 reset 出干净历史
            print("该仓库的所有提交都是涂鸦提交, 没有可保留的历史。")
            print("建议: 直接删除远程仓库重建, 或手动处理。已中止, 未做任何修改。")
            return
        else:
            # 情况2: 涂鸦与正常提交交错, 用 filter-branch 剔除
            print("涂鸦提交与正常提交交错, 使用 filter-branch 重写历史...")
            env_fb = dict(os.environ, FILTER_BRANCH_SQUELCH_WARNING="1")
            git(repo, "filter-branch", "-f", "--prune-empty",
                "--index-filter", f"git rm -rq --cached --ignore-unmatch {target}",
                "--", branch, env=env_fb)

        after = int(git(repo, "rev-list", "--count", "HEAD").stdout.strip())
        print(f"\n擦除完成: {before} -> {after} 个提交 (移除 {before - after} 个涂鸦提交)")

        if args.push:
            print(f"force push {branch} ...")
            git(repo, "push", "--force", "origin", branch, check=False)
            print("已强推。")
        else:
            print(f"提示: 确认无误后手动强推  git -C {repo} push --force origin {branch}")
        print("注意: GitHub 热力图重算需要几分钟到 24 小时, 旧格子才会变灰,")
        print("      之后再生成新单词即可干净覆盖。")
        return

    # ---------------- 生成提交 ----------------
    tz = time.strftime("%z") or "+0000"
    if args.seed is not None:
        random.seed(args.seed)
    count = 0
    graff_file = None
    if args.real_files:
        graff_dir = os.path.join(repo, "graffiti")
        os.makedirs(graff_dir, exist_ok=True)
        graff_file = os.path.join(graff_dir, f"{args.word.strip().lower().replace(' ', '_') or 'graffiti'}.html")
        if not os.path.exists(graff_file):
            with open(graff_file, "w", encoding="utf-8") as f:
                f.write(f"<!-- graffiti {args.word} - generated by github-graffiti -->\n")

    # 防封: 每天的时间戳从工作时间窗口内随机抽取, 避免机器般的等间隔网格
    def fmt_time(secs):
        hh, rest = divmod(secs, 3600)
        mm, ss = divmod(rest, 60)
        return f"{hh:02d}:{mm:02d}:{ss:02d}"

    for d, r, c in sorted(pixels):
        n = args.commits_per_pixel
        if args.stealth:
            # 随机时刻 (9:00~23:00 窗口内采样, 不重复, 乱序后使用更像人)
            times = random.sample(range(9 * 3600, 23 * 3600), min(n, 14 * 3600))
            random.shuffle(times)
        else:
            # 均匀铺满全天
            times = [(k * 86400) // max(n, 1) for k in range(n)]
        for k in range(n):
            dt = f"{d.isoformat()}T{fmt_time(times[k])} {tz}"
            env = dict(os.environ,
                       GIT_AUTHOR_DATE=dt,
                       GIT_COMMITTER_DATE=dt)
            if args.stealth:
                fname = os.path.basename(graff_file) if graff_file else "code"
                msg = random.choice(COMMIT_MSG_POOL).format(file=fname)
            else:
                msg = f"graffiti: {args.word} [{d.isoformat()} r{r}c{c} #{k+1}]"
            if graff_file:
                with open(graff_file, "a", encoding="utf-8") as f:
                    # 防封: 每次追加的行数/内容随机, 避免整齐划一
                    lines = random.randint(1, 5) if args.stealth else 1
                    for _ in range(lines):
                        f.write(f"<!-- {random.randint(1000, 9999)} {d.isoformat()} -->\n")
                git(repo, "add", graff_file)
                git(repo, "commit", "-m", msg, env=env)
            else:
                git(repo, "commit", "--allow-empty", "-m", msg, env=env)
            count += 1

    print(f"\n完成! 已生成 {count} 个提交于 {repo}")

    if args.push:
        branch = git(repo, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        if args.stealth and count > args.push_batch:
            # 防封: 分批推送, 批间随机延时 3~8 秒, 避免瞬时大量推送触发限流
            # 找到远程起点 (origin/branch 或首个提交)
            rp = git(repo, "rev-parse", f"origin/{branch}", check=False)
            base = rp.stdout.strip() if rp.returncode == 0 else ""
            if not base:
                base = git(repo, "rev-list", "--max-parents=0", "HEAD").stdout.strip().splitlines()[-1]
            commits = [c for c in git(repo, "rev-list", "--reverse", f"{base}..HEAD").stdout.split() if c]
            total = len(commits)
            print(f"分批推送 {branch}: 共 {total} 个提交, 每批 {args.push_batch} 个")
            for i in range(0, len(commits), args.push_batch):
                batch_end = commits[min(i + args.push_batch, len(commits)) - 1]
                git(repo, "push", "origin", f"{batch_end}:refs/heads/{branch}", check=False)
                done = min(i + args.push_batch, len(commits))
                print(f"  已推送 {done}/{len(commits)}")
                if done < len(commits):
                    wait = random.uniform(3, 8)
                    print(f"  等待 {wait:.1f}s ...")
                    time.sleep(wait)
            git(repo, "push", "-u", "origin", branch, check=False)
        else:
            print(f"推送 {branch} 到远程...")
            git(repo, "push", "-u", "origin", branch, check=False)
            print("已推送。")
    else:
        print(f"提示: 手动推送请运行  git -C {repo} push -u origin main")

    print("\n注意: 提交邮箱必须是绑定在你 GitHub 账号上的邮箱, 否则热力图不会计数。")
    print(f"当前仓库提交邮箱: {git(repo, 'config', 'user.email').stdout.strip() or '(未设置, 使用全局配置)'}")


if __name__ == "__main__":
    main()
