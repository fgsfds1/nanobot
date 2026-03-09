from pathlib import Path

from nanobot.config.loader import set_data_dir, set_config_path
from nanobot.config.paths import (
    get_bridge_install_dir,
    get_cli_history_path,
    get_cron_dir,
    get_data_dir,
    get_legacy_sessions_dir,
    get_logs_dir,
    get_media_dir,
    get_runtime_subdir,
    get_workspace_path,
)


def test_runtime_dirs_follow_data_dir(monkeypatch, tmp_path: Path) -> None:
    data_dir = tmp_path / "instance-a" / "data"
    set_data_dir(data_dir)

    assert get_data_dir() == data_dir
    assert get_runtime_subdir("cron") == data_dir / "cron"
    assert get_cron_dir() == data_dir / "cron"
    assert get_logs_dir() == data_dir / "logs"


def test_media_dir_supports_channel_namespace(monkeypatch, tmp_path: Path) -> None:
    data_dir = tmp_path / "instance-b" / "data"
    set_data_dir(data_dir)

    assert get_media_dir() == data_dir / "media"
    assert get_media_dir("telegram") == data_dir / "media" / "telegram"


def test_shared_and_legacy_paths_remain_global() -> None:
    assert get_cli_history_path() == Path.home() / ".nanobot" / "history" / "cli_history"
    assert get_bridge_install_dir() == Path.home() / ".nanobot" / "bridge"
    assert get_legacy_sessions_dir() == Path.home() / ".nanobot" / "sessions"


def test_workspace_path_is_under_data_dir(monkeypatch, tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    set_data_dir(data_dir)

    assert get_workspace_path() == data_dir / "workspace"
    assert get_workspace_path("~/custom-workspace") == Path.home() / "custom-workspace"


def test_data_dir_env_var_takes_precedence(monkeypatch, tmp_path: Path) -> None:
    data_dir = tmp_path / "env-data"
    set_data_dir(tmp_path / "explicit-data")
    monkeypatch.setenv("NANOBOT_DATA_DIR", str(data_dir))

    assert get_data_dir() == data_dir
