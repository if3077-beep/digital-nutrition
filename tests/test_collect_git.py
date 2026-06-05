import subprocess
import pytest
from datetime import datetime
from pathlib import Path
from digital_nutrition.sources.git import (
    find_git_repos,
    parse_git_log_output,
    parse_git_combined_output,
    parse_git_shortstat,
    classify_commit,
    _estimate_duration_from_diff,
    read_git_activity,
)


def test_parse_git_log_output_basic():
    """测试 git log 解析"""
    sample_output = 'abc123|Alice|2024-06-01 10:00:00 +0800|feat: add login'
    commits = parse_git_log_output(sample_output)
    assert len(commits) == 1
    c = commits[0]
    assert c["hash"] == "abc123"
    assert c["author"] == "Alice"
    assert c["message"] == "feat: add login"


def test_parse_git_log_output_multi():
    """测试多条 commit 解析"""
    sample = (
        'hash1|Alice|2024-06-01 10:00:00 +0800|feat: a\n'
        'hash2|Bob|2024-06-02 10:00:00 +0800|fix: b\n'
    )
    commits = parse_git_log_output(sample)
    assert len(commits) == 2
    assert commits[0]["author"] == "Alice"
    assert commits[1]["author"] == "Bob"


def test_parse_git_log_output_empty():
    """空输出"""
    assert parse_git_log_output("") == []
    assert parse_git_log_output("\n\n") == []


# ===== v0.5.9: parse_git_combined_output（单次 git log 解析）=====

def test_parse_git_combined_output_basic():
    """基本：---HASH: 前缀 + 下一行 shortstat"""
    sample = (
        "---HASH:abc123|Alice|2024-06-01 10:00:00 +0800|feat: a\n"
        " 1 file changed, 5 insertions(+), 2 deletions(-)\n"
        "\n"
        "---HASH:def456|Bob|2024-06-02 10:00:00 +0800|fix: b\n"
        " 3 files changed, 50 insertions(+), 10 deletions(-)\n"
    )
    result = parse_git_combined_output(sample)
    assert len(result) == 2
    assert result[0] == {
        "hash": "abc123", "author": "Alice",
        "timestamp": "2024-06-01 10:00:00 +0800",
        "message": "feat: a", "insertions": 5, "deletions": 2,
    }
    assert result[1] == {
        "hash": "def456", "author": "Bob",
        "timestamp": "2024-06-02 10:00:00 +0800",
        "message": "fix: b", "insertions": 50, "deletions": 10,
    }


def test_parse_git_combined_output_no_shortstat():
    """commit 没有 shortstat（边界情况）"""
    sample = (
        "---HASH:abc123|Alice|2024-06-01 10:00:00 +0800|fix: empty\n"
        "\n"
    )
    result = parse_git_combined_output(sample)
    assert len(result) == 1
    assert result[0]["insertions"] == 0
    assert result[0]["deletions"] == 0


def test_parse_git_combined_output_empty():
    """空输出"""
    assert parse_git_combined_output("") == []
    assert parse_git_combined_output("\n\n") == []


# ===== v0.5.8: parse_git_shortstat + _estimate_duration_from_diff =====

def test_parse_git_shortstat_basic():
    """解析 git log --shortstat 输出"""
    sample = (
        "HASHSTAT:abc123\n"
        " 1 file changed, 5 insertions(+), 2 deletions(-)\n"
        "\n"
        "HASHSTAT:def456\n"
        " 3 files changed, 50 insertions(+), 10 deletions(-)\n"
    )
    result = parse_git_shortstat(sample)
    assert result == {
        "abc123": (5, 2),
        "def456": (50, 10),
    }


def test_parse_git_shortstat_no_changes():
    """空 commit（merge 过滤后可能没数据）"""
    assert parse_git_shortstat("") == {}


def test_parse_git_shortstat_only_insertions():
    """只有 insertions 没有 deletions（边界情况）"""
    sample = (
        "HASHSTAT:abc123\n"
        " 2 files changed, 30 insertions(+)\n"
    )
    result = parse_git_shortstat(sample)
    assert result == {"abc123": (30, 0)}


def test_estimate_duration_from_diff_tiers():
    """行数 → 时长分档（<10=10m, 10-100=30m, >100=60m）"""
    # < 10 lines → 10 min
    assert _estimate_duration_from_diff(5, 2) == 10 * 60
    assert _estimate_duration_from_diff(0, 0) == 10 * 60  # 边界：0 行也算
    # 10-100 lines → 30 min
    assert _estimate_duration_from_diff(10, 0) == 30 * 60
    assert _estimate_duration_from_diff(50, 50) == 30 * 60
    assert _estimate_duration_from_diff(100, 0) == 30 * 60  # 边界：100 行
    # > 100 lines → 60 min
    assert _estimate_duration_from_diff(100, 1) == 60 * 60  # 101 行
    assert _estimate_duration_from_diff(500, 200) == 60 * 60


def test_classify_commit_feat():
    """feat 类型 → code"""
    assert classify_commit("feat: add user auth") == "code"
    assert classify_commit("feature: new dashboard") == "code"
    assert classify_commit("feat(api): add endpoint") == "code"


def test_classify_commit_docs():
    """docs 类型 → learning"""
    assert classify_commit("docs: update README") == "learning"
    assert classify_commit("documentation: add API docs") == "learning"


def test_classify_commit_fix():
    """fix 类型 → code"""
    assert classify_commit("fix: bug in login") == "code"
    assert classify_commit("bugfix: resolve crash") == "code"


def test_classify_commit_chore():
    """chore/build → work"""
    assert classify_commit("chore: update deps") == "work"
    assert classify_commit("build: fix CI") == "work"
    assert classify_commit("ci: update workflow") == "work"


def test_classify_commit_refactor():
    """refactor/test/perf → code"""
    assert classify_commit("refactor: clean up utils") == "code"
    assert classify_commit("test: add unit tests") == "code"
    assert classify_commit("perf: optimize query") == "code"


def test_classify_commit_unknown():
    """未知类型 → code（默认）"""
    assert classify_commit("random message") == "code"


def test_classify_commit_keyword_fallback():
    """关键词兜底分类"""
    assert classify_commit("Update readme for clarity") == "learning"  # 包含 readme
    assert classify_commit("Deploy to production") == "work"  # 包含 deploy


def test_read_git_activity_real_repo(tmp_path):
    """在临时 git 仓库中测试读取"""
    repo = tmp_path / "test_repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True, capture_output=True)

    # 创建一个 commit
    (repo / "test.txt").write_text("hello")
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "feat: add test file"], cwd=repo, check=True, capture_output=True)

    events = read_git_activity(repo, since=None)
    assert len(events) == 1
    assert events[0].source == "git"
    assert events[0].category == "code"
    assert "feat" in events[0].title
    # v0.5.8：duration 由 diff 行数决定
    # 1 file, 1 line（"hello"）→ total=1 < 10 → 10 min
    assert events[0].duration_seconds == 10 * 60


def test_read_git_activity_large_diff_60min(tmp_path):
    """大 commit (>100 lines) → 60 min"""
    repo = tmp_path / "test_repo_big"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=repo, check=True, capture_output=True)
    # 200 行
    (repo / "big.txt").write_text("\n".join(f"line {i}" for i in range(200)))
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "feat: add big file"], cwd=repo, check=True, capture_output=True)

    events = read_git_activity(repo, since=None)
    assert len(events) == 1
    # 200 lines > 100 → 60 min
    assert events[0].duration_seconds == 60 * 60


def test_read_git_activity_not_a_repo(tmp_path):
    """非 git 目录返回空列表"""
    fake_repo = tmp_path / "not_a_repo"
    fake_repo.mkdir()
    events = read_git_activity(fake_repo, since=None)
    assert events == []


def test_find_git_repos_finds_subdirs(tmp_path):
    """查找目录下的 git 仓库"""
    repo1 = tmp_path / "repo1"
    repo2 = tmp_path / "subdir" / "repo2"
    for r in [repo1, repo2]:
        r.mkdir(parents=True)
        (r / ".git").mkdir()

    repos = find_git_repos(tmp_path)
    assert len(repos) == 2
    assert repo1 in repos
    assert repo2 in repos
