# Fix for Issue #984: Media Path Outside Workspace

## Problem

When `restrictToWorkspace: true` is configured in nanobot, the file system tools (read_file, write_file, edit_file, list_dir) are restricted to only access files within the workspace directory. However, Telegram media files (images, voice messages, documents) were being saved to `~/.nanobot/media/`, which is **outside the workspace**.

This caused two issues:
1. **Multimodal models couldn't "see" images** - The agent could only read the filename, not the actual image content
2. **Skills couldn't process media** - Any skill that needed to read media files (like Whisper for transcription) was blocked

## Root Cause

- **telegram.py line 369**: Media was hardcoded to save to `Path.home() / ".nanobot" / "media"`
- **loop.py line 118**: When `restrict_to_workspace=True`, `allowed_dir=self.workspace` was set
- **filesystem.py line 14-20**: The `_resolve_path` function checked if paths were within `allowed_dir` and raised `PermissionError` if not

## Solution

Modified the Telegram channel to save media inside the workspace when `restrictToWorkspace` is enabled:

### Changes Made

1. **telegram.py** - Added `workspace` parameter to `TelegramChannel.__init__()`:
   - Line 182: Added `workspace: Path | None = None` parameter
   - Line 185: Store workspace path as instance variable
   - Line 369-374: Modified media download logic to use workspace path when provided, otherwise fall back to `~/.nanobot/media/`

2. **manager.py** - Pass workspace path to TelegramChannel:
   - Line 24-28: Check if `restrict_to_workspace` is enabled and pass workspace path accordingly

### Code Changes

**telegram.py:**
```python
def __init__(
    self,
    config: TelegramConfig,
    bus: MessageBus,
    groq_api_key: str = "",
    workspace: Path | None = None,  # NEW
):
    super().__init__(config, bus)
    self.config: TelegramConfig = config
    self.groq_api_key = groq_api_key
    self.workspace = workspace  # NEW: Workspace path for media storage

# ... later in _on_message() ...

# Save to workspace/media/ if workspace is provided (for restrictToWorkspace support)
# Otherwise fall back to ~/.nanobot/media/
if self.workspace:
    media_dir = self.workspace / "media"
else:
    media_dir = Path.home() / ".nanobot" / "media"
media_dir.mkdir(parents=True, exist_ok=True)
```

**manager.py:**
```python
# Telegram channel
if self.config.channels.telegram.enabled:
    try:
        from nanobot.channels.telegram import TelegramChannel
        # Pass workspace path for restrictToWorkspace support
        workspace = self.config.workspace_path if self.config.tools.restrict_to_workspace else None
        self.channels["telegram"] = TelegramChannel(
            self.config.channels.telegram,
            self.bus,
            groq_api_key=self.config.providers.groq.api_key,
            workspace=workspace,  # NEW
        )
```

## Behavior

### Before Fix
- Media always saved to: `~/.nanobot/media/<filename>`
- With `restrictToWorkspace: true`: Agent **cannot access** media files
- Without `restrictToWorkspace: true`: Agent **can access** media files

### After Fix
- With `restrictToWorkspace: true`: Media saved to `<workspace>/media/<filename>` - Agent **can access** ✓
- Without `restrictToWorkspace: true`: Media saved to `~/.nanobot/media/<filename>` - Agent **can access** ✓

## Testing

To test the fix:

1. **Enable restrictToWorkspace** in config:
   ```json
   {
     "tools": {
       "restrictToWorkspace": true
     }
   }
   ```

2. **Send an image** to the Telegram bot

3. **Verify** the agent can:
   - See the image (for multimodal models)
   - Read the image file using `read_file` tool
   - Process the image with skills

4. **Check** the media file location:
   - Should be in `<workspace>/media/` instead of `~/.nanobot/media/`

## Files Modified

- `nanobot/channels/telegram.py` - Added workspace parameter and conditional media path
- `nanobot/channels/manager.py` - Pass workspace path to TelegramChannel

## Backward Compatibility

This fix is **fully backward compatible**:
- When `restrictToWorkspace: false` (default), behavior is unchanged
- When `restrictToWorkspace: true`, media is now accessible (fixes the bug)
- No breaking changes to API or configuration

## Future Considerations

Other channels (Discord, WhatsApp, etc.) may have similar issues if they download media. They should be checked and updated similarly if needed.