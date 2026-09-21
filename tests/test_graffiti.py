#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""graffiti.py 的测试。

只用标准库 (unittest), 不需要装任何东西:

    python3 -m unittest discover -s tests -v

测试都在临时目录里建自己的 git 仓库, 不会碰 ./repo 或 ./profile-repo。
"""

import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "graffiti.py")
sys.path.insert(0, ROOT)

import graffiti  # noqa: E402


def run(*args, cwd=None, expect_ok=True):
    """跑一次 graffiti.py"""
    cmd = [sys.executable, SCRIPT] + [str(a) for a in args]
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if expect_ok and r.returncode != 0:
        raise AssertionError(
            f"命令失败: {' '.join(cmd)}\n"
            f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}"
        )
    return r


def git(repo, *args):
    r = subprocess.run(["git", "-C", repo] + list(args),
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} 失败: {r.stderr}")
    return r.stdout


class TempRepoMixin:
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = os.path.join(self._tmp.name, "repo")

    def init_repo(self):
        """建一个配好提交身份的仓库"""
        os.makedirs(self.repo, exist_ok=True)
        git(self.repo, "init", "-b", "main")
        git(self.repo, "config", "user.name", "Test User")
        git(self.repo, "config", "user.email", "1234567+testuser@users.noreply.github.com")
        return self.repo

    def normal_commit(self, filename, content="hello\n", message=None):
        """提交一个普通文件 (模拟仓库里本来就有的正常提交)"""
        path = os.path.join(self.repo, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        git(self.repo, "add", filename)
        git(self.repo, "commit", "-m", message or f"add {filename}")
        return git(self.repo, "rev-parse", "HEAD").strip()

    def subjects(self):
        return git(self.repo, "log", "--format=%s").splitlines()

    def commit_dates(self):
        """所有提交的作者日期 (YYYY-MM-DD), 新的在前"""
        return git(self.repo, "log", "--format=%ad", "--date=short").splitlines()

    def count(self):
        return int(git(self.repo, "rev-list", "--count", "HEAD").strip())

    def tracked_files(self):
        return git(self.repo, "ls-tree", "-r", "--name-only", "HEAD").splitlines()


def expected_dates(word, weeks_ago):
    """按规格算出每个亮像素应该落在哪一天。

    热力图 52 列, 每列是一周 (周日开始)。单词最后一列离当前周 weeks_ago 周,
    所以宽度 W 的单词里, 第 c 列在 current_week_start - (weeks_ago + W-1-c) 周,
    第 r 行是那一周的第 r 天。
    """
    rows = graffiti.render_word(word)
    width = len(rows[0])
    today = date.today()
    current_week_start = today - timedelta(days=(today.weekday() + 1) % 7)
    out = set()
    for r in range(7):
        for c in range(width):
            if rows[r][c] == "#":
                week = current_week_start - timedelta(weeks=weeks_ago + (width - 1 - c))
                out.add((week + timedelta(days=r)).isoformat())
    return out


class TestFont(unittest.TestCase):
    """字库本身的形状约束"""

    def test_every_glyph_is_7_rows_of_6_chars(self):
        for ch, glyph in graffiti.FONT.items():
            with self.subTest(char=ch):
                self.assertEqual(len(glyph), 7, f"'{ch}' 应该正好 7 行")
                for row in glyph:
                    self.assertEqual(len(row), 6, f"'{ch}' 的每行应该是 6 个字符")

    def test_space_is_all_off(self):
        # 字形里 '#' 是亮, '.' 是暗; 每个字形第一个字符是左边距, 真正的 5 列在 [1:]
        for row in graffiti.FONT[" "]:
            self.assertEqual(row[1:], ".....")

    def test_glyph_bodies_use_only_dot_and_hash(self):
        for ch, glyph in graffiti.FONT.items():
            for row in glyph:
                with self.subTest(char=ch, row=row):
                    self.assertEqual(row[0], " ", f"'{ch}' 的左边距必须是空格")
                    self.assertTrue(set(row[1:]) <= {" ", ".", "#"},
                                    f"'{ch}' 只能画 '.', '#', ' '")

    def test_heart_has_pixels(self):
        self.assertGreater("".join(graffiti.FONT["@"]).count("#"), 0)


class TestRenderWord(unittest.TestCase):
    def test_single_letter_is_5_wide(self):
        rows = graffiti.render_word("A")
        self.assertEqual(len(rows), 7)
        self.assertTrue(all(len(r) == 5 for r in rows))

    def test_letters_get_one_column_gap(self):
        # n 个字符占 6n-1 列
        for word, width in [("LOVE", 23), ("AB", 11), ("A B", 17), ("HELLO", 29)]:
            with self.subTest(word=word):
                self.assertEqual(len(graffiti.render_word(word)[0]), width)

    def test_lowercase_is_uppercased(self):
        self.assertEqual(graffiti.render_word("love"), graffiti.render_word("LOVE"))

    def test_unsupported_char_exits(self):
        with self.assertRaises(SystemExit):
            graffiti.render_word("LÖVE")

    def test_unsupported_char_message_lists_charset(self):
        # SystemExit 里带的是提示信息, 应该告诉用户怎么查字库
        with self.assertRaises(SystemExit) as cm:
            graffiti.render_word("~")
        self.assertIn("show-font", str(cm.exception))


class TestGraffitiFilename(unittest.TestCase):
    def test_lowercased(self):
        self.assertEqual(graffiti.graffiti_filename("LOVE"), "graffiti/love.html")

    def test_spaces_become_underscores(self):
        self.assertEqual(graffiti.graffiti_filename("HI THERE"), "graffiti/hi_there.html")

    def test_matches_what_generation_actually_writes(self):
        # 擦除模式靠这个名字找文件, 必须和生成时写的一致
        for word in ["LOVE", "hi there", "2026"]:
            fname = os.path.basename(graffiti.graffiti_filename(word))
            with tempfile.TemporaryDirectory() as tmp:
                repo = os.path.join(tmp, "r")
                os.makedirs(repo)
                subprocess.run(["git", "-C", repo, "init", "-b", "main"],
                               capture_output=True)
                subprocess.run(["git", "-C", repo, "config", "user.email", "a@b.c"],
                               capture_output=True)
                subprocess.run(["git", "-C", repo, "config", "user.name", "t"],
                               capture_output=True)
                run("--word", word, "--repo", repo, "--real-files",
                    "--commits-per-pixel", "1", "--weeks-ago", "1")
                self.assertIn(f"graffiti/{fname}",
                              git(repo, "ls-tree", "-r", "--name-only", "HEAD").splitlines())


class TestPreview(TempRepoMixin, unittest.TestCase):
    def test_preview_creates_nothing(self):
        target = os.path.join(self._tmp.name, "should-not-exist")
        r = run("--word", "LOVE", "--repo", target, "--preview")
        self.assertFalse(os.path.exists(target))
        self.assertIn("LOVE", r.stdout)

    def test_preview_shows_all_seven_rows(self):
        r = run("--word", "LOVE", "--preview")
        for label in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]:
            self.assertIn(label, r.stdout)

    def test_long_word_warns_about_overflow(self):
        r = run("--word", "ABCDEFGHIJ", "--preview")
        self.assertIn("警告", r.stdout)


class TestMissingIdentity(TempRepoMixin, unittest.TestCase):
    def test_clear_error_when_no_commit_identity(self):
        # 全新仓库没配 user.email 时, 应该给出可操作的提示而不是 git 的原始报错
        os.makedirs(self.repo)
        git(self.repo, "init", "-b", "main")
        env = dict(os.environ, GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_SYSTEM="/dev/null")
        r = subprocess.run(
            [sys.executable, SCRIPT, "--word", "L", "--repo", self.repo,
             "--commits-per-pixel", "1"],
            capture_output=True, text=True, env=env)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("user.email", r.stdout + r.stderr)


class TestGenerate(TempRepoMixin, unittest.TestCase):
    def test_commit_count_is_pixels_times_commits_per_pixel(self):
        self.init_repo()
        # L 只点亮最左一列, 共 11 个像素
        pixels = "".join(graffiti.render_word("L")).count("#")
        self.assertEqual(pixels, 11)
        run("--word", "L", "--repo", self.repo, "--commits-per-pixel", "3")
        self.assertEqual(self.count(), 33)

    def test_dates_match_the_grid_geometry(self):
        """每个亮像素 (r, c) 都要落在它该在的那一天"""
        for word, weeks_ago in [("!", 1), ("L", 3), ("LOVE", 1), ("A.B", 6)]:
            with self.subTest(word=word):
                self.setUp()  # 每个 subTest 换一个干净仓库, 否则会叠加
                self.init_repo()
                run("--word", word, "--repo", self.repo, "--commits-per-pixel", "1",
                    "--weeks-ago", str(weeks_ago))
                self.assertEqual(set(self.commit_dates()),
                                 expected_dates(word, weeks_ago))

    def test_weeks_ago_shifts_the_whole_word(self):
        self.init_repo()
        run("--word", "!", "--repo", self.repo, "--commits-per-pixel", "1",
            "--weeks-ago", "5")
        self.assertEqual(set(self.commit_dates()), expected_dates("!", 5))

    def test_all_dates_are_in_the_past(self):
        self.init_repo()
        run("--word", "LOVE", "--repo", self.repo, "--commits-per-pixel", "2")
        self.assertTrue(all(d < date.today().isoformat()
                            for d in self.commit_dates()))

    def test_real_files_commits_a_file_not_empty_commits(self):
        self.init_repo()
        run("--word", "LOVE", "--repo", self.repo, "--real-files",
            "--commits-per-pixel", "1")
        self.assertIn("graffiti/love.html", self.tracked_files())

    def test_empty_commits_when_not_real_files(self):
        self.init_repo()
        run("--word", "LOVE", "--repo", self.repo, "--commits-per-pixel", "1")
        self.assertEqual(self.tracked_files(), [])

    def test_commit_message_records_the_pixel(self):
        self.init_repo()
        run("--word", "L", "--repo", self.repo, "--commits-per-pixel", "1")
        self.assertTrue(all(s.startswith("graffiti: L [") for s in self.subjects()))

    def test_seed_makes_it_reproducible(self):
        dates = []
        times = []
        for _ in range(2):
            with tempfile.TemporaryDirectory() as tmp:
                repo = os.path.join(tmp, "repo")
                os.makedirs(repo)
                git(repo, "init", "-b", "main")
                git(repo, "config", "user.email", "a@b.c")
                git(repo, "config", "user.name", "t")
                run("--word", "LOVE", "--repo", repo, "--stealth", "--seed", "42",
                    "--real-files", "--commits-per-pixel", "3")
                out = git(repo, "log", "--format=%ad|%s", "--date=iso")
                dates.append(out)
        self.assertEqual(dates[0], dates[1])

    def test_different_seeds_differ(self):
        outs = []
        for seed in ["1", "2"]:
            with tempfile.TemporaryDirectory() as tmp:
                repo = os.path.join(tmp, "repo")
                os.makedirs(repo)
                git(repo, "init", "-b", "main")
                git(repo, "config", "user.email", "a@b.c")
                git(repo, "config", "user.name", "t")
                run("--word", "LOVE", "--repo", repo, "--stealth", "--seed", seed,
                    "--real-files", "--commits-per-pixel", "3")
                outs.append(git(repo, "log", "--format=%ad|%s", "--date=iso"))
        self.assertNotEqual(outs[0], outs[1])


class TestStealth(TempRepoMixin, unittest.TestCase):
    def test_messages_come_from_the_pool(self):
        self.init_repo()
        run("--word", "!", "--repo", self.repo, "--stealth", "--real-files",
            "--commits-per-pixel", "1")
        pool = {m.format(file="!.html") for m in graffiti.COMMIT_MSG_POOL}
        for s in self.subjects():
            self.assertIn(s, pool)

    def test_message_format_gives_nothing_away(self):
        """防封的关键: 提交信息里不能出现 "graffiti: <WORD>" 这种机器指纹

        注意: --real-files 会把单词写进文件名 (graffiti/love.html), 而
        --stealth 的模板里有 "update {file}", 所以文件名本身还是会出现在日志里。
        想连文件名都不暴露, 就别用 --real-files。
        """
        self.init_repo()
        run("--word", "LOVE", "--repo", self.repo, "--stealth", "--real-files",
            "--commits-per-pixel", "1")
        for s in self.subjects():
            self.assertFalse(s.upper().startswith("GRAFFITI: "), s)

    def test_empty_commits_also_hide_the_word(self):
        self.init_repo()
        run("--word", "LOVE", "--repo", self.repo, "--stealth",
            "--commits-per-pixel", "1")
        for s in self.subjects():
            self.assertNotIn("LOVE", s.upper())
            self.assertFalse(s.upper().startswith("GRAFFITI: "), s)

    def test_timestamps_are_randomised_within_working_hours(self):
        self.init_repo()
        run("--word", "!", "--repo", self.repo, "--stealth", "--real-files",
            "--seed", "7", "--commits-per-pixel", "5", "--weeks-ago", "1")
        # 同一天的 5 个提交应该都落在 9:00-23:00, 且互不相同
        stamps = git(self.repo, "log", "--format=%ad", "--date=iso").splitlines()
        by_day = {}
        for s in stamps:
            day, rest = s.split(" ", 1)
            by_day.setdefault(day, []).append(rest[:8])
        self.assertEqual(len(by_day), 6)  # '!' 点亮的 6 天
        for day, times in by_day.items():
            with self.subTest(day=day):
                self.assertEqual(len(times), 5)
                self.assertEqual(len(set(times)), 5, "同一天的时刻重复了")
                for t in times:
                    self.assertGreaterEqual(t, "09:00")
                    self.assertLess(t, "23:00")

    def test_non_stealth_timestamps_are_spread_evenly(self):
        """不加 --stealth 时, 同一天的提交是等间隔铺满全天的"""
        self.init_repo()
        run("--word", "!", "--repo", self.repo, "--commits-per-pixel", "4",
            "--weeks-ago", "1")
        by_day = {}
        for s in git(self.repo, "log", "--format=%ad", "--date=iso").splitlines():
            day, clock = s.split(" ")[:2]
            by_day.setdefault(day, []).append(clock)
        self.assertEqual(len(by_day), 6)  # '!' 点亮的 6 天
        for day, times in by_day.items():
            with self.subTest(day=day):
                self.assertEqual(sorted(times),
                                 ["00:00:00", "06:00:00", "12:00:00", "18:00:00"])


class TestErase(TempRepoMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.init_repo()

    def test_erase_word_at_the_tail_resets(self):
        self.normal_commit("README.md", "base\n")
        base = self.count()
        run("--word", "L", "--repo", self.repo, "--real-files",
            "--commits-per-pixel", "1")
        self.assertEqual(self.count(), base + 11)

        r = run("--word", "L", "--repo", self.repo, "--erase")
        self.assertIn("reset", r.stdout)
        self.assertEqual(self.count(), base)
        self.assertEqual(self.subjects(), ["add README.md"])

    def test_erase_keeps_normal_commits_that_came_after(self):
        """涂鸦和正常提交交错时, 正常提交必须原样保留

        注意: 涂鸦提交被抽掉后, 它后面那些提交的父提交变了, sha 必然跟着变 ——
        这是重写历史的固有代价, 能保住的是内容和作者时间。
        """
        self.normal_commit("README.md", "base\n")
        run("--word", "!", "--repo", self.repo, "--real-files",
            "--commits-per-pixel", "1")
        self.normal_commit("app.py", "print(1)\n", message="add app.py")
        after_date = self.commit_dates()[0]

        r = run("--word", "!", "--repo", self.repo, "--erase")
        self.assertIn("filter-branch", r.stdout)

        self.assertEqual(self.subjects(), ["add app.py", "add README.md"])
        self.assertEqual(self.tracked_files(), ["README.md", "app.py"])
        # 被保留的提交, 内容与作者日期都不该变
        self.assertEqual(git(self.repo, "show", "HEAD:app.py"), "print(1)\n")
        self.assertEqual(self.commit_dates()[0], after_date)

    def test_erase_preserves_author_dates_of_surviving_commits(self):
        self.normal_commit("README.md", "base\n")
        before = self.commit_dates()
        run("--word", "L", "--repo", self.repo, "--real-files",
            "--commits-per-pixel", "1")
        self.normal_commit("app.py", "print(1)\n", message="add app.py")
        run("--word", "L", "--repo", self.repo, "--erase")
        # order 是新的在前: add app.py, add README.md
        self.assertEqual(self.commit_dates()[1], before[0])

    def test_erase_does_not_touch_another_word(self):
        """回归测试: 擦旧词不能顺手把后画的词也 reset 掉"""
        self.normal_commit("README.md", "base\n")
        run("--word", "L", "--repo", self.repo, "--real-files",
            "--commits-per-pixel", "1", "--weeks-ago", "6")
        run("--word", "O", "--repo", self.repo, "--real-files",
            "--commits-per-pixel", "1", "--weeks-ago", "1")
        self.assertIn("graffiti/o.html", self.tracked_files())

        run("--word", "L", "--repo", self.repo, "--erase")

        self.assertIn("graffiti/o.html", self.tracked_files(),
                      "擦 L 把后面画的 O 也删掉了")
        self.assertNotIn("graffiti/l.html", self.tracked_files())

    def test_erase_handles_empty_commits_by_message(self):
        """没加 --real-files 画的词只有提交信息可认, 也要能擦掉"""
        self.normal_commit("README.md", "base\n")
        base = self.count()
        run("--word", "L", "--repo", self.repo, "--commits-per-pixel", "1")
        self.assertEqual(self.count(), base + 11)

        r = run("--word", "L", "--repo", self.repo, "--erase")
        self.assertNotIn("没有找到", r.stdout)
        self.assertEqual(self.count(), base)

    def test_erase_unknown_word_is_a_noop(self):
        self.normal_commit("README.md", "base\n")
        base = self.count()
        r = run("--word", "Z", "--repo", self.repo, "--erase")
        self.assertIn("没有找到", r.stdout)
        self.assertEqual(self.count(), base)

    def test_erase_all_graffiti_aborts_cleanly(self):
        """整个仓库只有涂鸦提交时, 不能把历史清空"""
        run("--word", "L", "--repo", self.repo, "--real-files",
            "--commits-per-pixel", "1")
        base = self.count()
        r = run("--word", "L", "--repo", self.repo, "--erase")
        self.assertIn("没有可保留的历史", r.stdout)
        self.assertEqual(self.count(), base)

    def test_erase_on_empty_repo_is_a_noop(self):
        r = run("--word", "L", "--repo", self.repo, "--erase")
        self.assertIn("还没有任何提交", r.stdout)

    def test_message_matching_is_not_a_regex(self):
        """单词里的 . 不能被当成正则通配, 否则擦 A.B 会连 AXB 一起误伤"""
        self.normal_commit("README.md", "base\n")
        run("--word", "A.B", "--repo", self.repo, "--commits-per-pixel", "1",
            "--weeks-ago", "1")
        run("--word", "AXB", "--repo", self.repo, "--commits-per-pixel", "1",
            "--weeks-ago", "8")

        axb_commits = "".join(graffiti.render_word("AXB")).count("#")
        self.assertEqual(
            len([s for s in self.subjects() if s.startswith("graffiti: AXB [")]),
            axb_commits)

        run("--word", "A.B", "--repo", self.repo, "--erase")

        remaining = [s for s in self.subjects() if s.startswith("graffiti: AXB [")]
        self.assertEqual(len(remaining), axb_commits, "AXB 的提交被误删了")
        self.assertEqual([s for s in self.subjects()
                          if s.startswith("graffiti: A.B [")], [])


class TestWorkflow(unittest.TestCase):
    """workflow 的回归护栏 —— 这几条都是踩过的坑"""

    def setUp(self):
        path = os.path.join(ROOT, ".github", "workflows", "graffiti.yml")
        with open(path, encoding="utf-8") as f:
            self.text = f.read()

    def test_target_checkout_does_not_persist_credentials(self):
        """checkout 留下 token 会和手工 extraheader 叠成两个 Authorization 头"""
        self.assertIn("persist-credentials: false", self.text)

    def test_pat_is_masked(self):
        self.assertIn("::add-mask::", self.text)

    def test_pat_never_goes_into_a_remote_url(self):
        for line in self.text.splitlines():
            if "remote" in line and "set-url" in line:
                self.assertNotIn("GRAFFITI_PAT", line,
                                 "token 拼进 remote URL 会在 push 失败时泄露到日志")

    def test_missing_pat_fails_with_a_clear_message(self):
        self.assertIn("GRAFFITI_PAT", self.text)
        self.assertIn("::error::", self.text)

    def test_both_erase_and_draw_steps_exist(self):
        self.assertIn("--erase", self.text)
        self.assertIn("--push", self.text)

    def test_is_a_valid_yaml_subset(self):
        """没有 PyYAML, 只做最基本的缩进/键值检查"""
        self.assertNotIn("\t", self.text, "YAML 里不能用 tab 缩进")
        self.assertTrue(self.text.startswith("name:"))
        self.assertIn("workflow_dispatch:", self.text)


if __name__ == "__main__":
    unittest.main()
