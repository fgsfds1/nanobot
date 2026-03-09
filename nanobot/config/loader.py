"""Configuration loading utilities."""

import json
from pathlib import Path

from nanobot.config.schema import Config


# Global variables (for multi-instance support)
_current_config_path: Path | None = None
_current_data_dir: Path | None = None


def set_config_path(path: Path) -> None:
    """Set the current config path."""
    global _current_config_path
    _current_config_path = path


def get_config_path() -> Path:
    """Get the configuration file path."""
    if _current_config_path:
        return _current_config_path
    return Path.home() / ".nanobot" / "config.json"


def set_data_dir(path: Path) -> None:
    """Set the data directory explicitly."""
    global _current_data_dir
    _current_data_dir = path


def get_data_dir() -> Path:
    """Get the data directory.

    Priority: NANOBOT_DATA_DIR env var > explicit set_data_dir() > config_path.parent
    """
    import os

    env_dir = os.environ.get("NANOBOT_DATA_DIR")
    if env_dir:
        return Path(env_dir).expanduser()
    if _current_data_dir:
        return _current_data_dir
    return get_config_path().parent


def load_config(config_path: Path | None = None) -> Config:
    """
    Load configuration from file or create default.

    Args:
        config_path: Optional path to config file. Uses default if not provided.

    Returns:
        Loaded configuration object.
    """
    import sys

    path = config_path or get_config_path()

    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            data, migrated = _migrate_config(data, path)

            # If migration occurred, save the updated config back to disk
            if migrated:
                print(
                    f"Config migrated: workspace → data_dir in {path}",
                    file=sys.stderr,
                )
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

            return Config.model_validate(data)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Warning: Failed to load config from {path}: {e}")
            print("Using default configuration.")

    return Config()


def save_config(config: Config, config_path: Path | None = None) -> None:
    """
    Save configuration to file.

    Args:
        config: Configuration to save.
        config_path: Optional path to save to. Uses default if not provided.
    """
    path = config_path or get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    data = config.model_dump(by_alias=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _migrate_config(data: dict, config_path: Path) -> tuple[dict, bool]:
    """Migrate old config formats to current.

    Returns:
        (migrated_data, migration_occurred)
    """
    import sys

    migrated = False

    # Move tools.exec.restrictToWorkspace → tools.restrictToWorkspace
    tools = data.get("tools", {})
    exec_cfg = tools.get("exec", {})
    if "restrictToWorkspace" in exec_cfg and "restrictToWorkspace" not in tools:
        tools["restrictToWorkspace"] = exec_cfg.pop("restrictToWorkspace")

    # Migrate agents.defaults.workspace to data_dir (if not already set)
    if "data_dir" not in data:
        agents = data.setdefault("agents", {})
        defaults = agents.setdefault("defaults", {})
        workspace = defaults.get("workspace")

        if workspace:
            ws_path = Path(workspace).expanduser()

            # Only migrate if workspace follows the <data_dir>/workspace convention
            # 1. Must be named "workspace"
            # 2. Parent must match config file's parent directory
            if ws_path.name == "workspace" and ws_path.parent == config_path.parent:
                data["data_dir"] = str(ws_path.parent)
                # Remove the old workspace field from config
                defaults.pop("workspace", None)
                migrated = True
            else:
                print(
                    f"Warning: Could not auto-migrate workspace path '{workspace}'.",
                    file=sys.stderr,
                )
                print(
                    f"         Please set 'data_dir' manually in {config_path}",
                    file=sys.stderr,
                )

    return data, migrated
