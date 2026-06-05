import subprocess
import pytest
from datetime import datetime
from pathlib import Path
from digital_nutrition.sources.git import (
    find_git_repos,
    parse_git_log_output,
    classify_commit,
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
    assert events[0].duration_seconds in (1800, 3600)  # 工作日 30m 或周末 1h


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
