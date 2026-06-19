# Production UX TODO

Goal: keep the current working video result and make the interface understandable without explaining it to the user.

## Principle

The current v15 pipeline works. Production work must not change the video result unless explicitly required. UI changes must expose the working model more clearly.

## Must do before production

| Area | Problem | Required change |
|---|---|---|
| First launch | User does not know the correct working scenario | Add a simple first-run setup flow: camera, virtual camera, shape, chroma, dynamic crop |
| Modes | Too many technical words | Show 3 visible modes: Simple camera, Chroma key, Face auto-crop |
| Dynamic crop | Parameters are powerful but not intuitive | Add presets: Stable portrait, Fast tracking, Manual fine tune |
| Chroma key | Pipettes and HSV are expert-level | Add a guided action: Pick background, adjust tolerance, preview mask |
| Virtual camera | User may not understand whether output is live | Add a clear status badge: Off / Starting / Live / Error |
| Camera switching | Camera numbers are unclear | Prefer camera aliases and show resolution/FPS next to each camera |
| Error states | Failures are hidden in logs | Surface camera/vcam errors directly in UI with recovery action |
| Settings | Too many knobs at once | Split into Basic / Advanced sections |
| Presets | Known-good settings are not reusable | Add preset import/export and reset to known-good baseline |
| Release confidence | Manual checks are scattered | Add production checklist and smoke-test script |

## Should do after production candidate

| Area | Change |
|---|---|
| Hotkeys | Add editable hotkey overview with conflict warnings |
| Logs | Add Open logs folder action |
| Diagnostics | Add Copy diagnostics button |
| PTZ | Keep behind Advanced/Experimental flag |
| About window | Add version, repo link, support/contact, build date |

## Do not do before production

| Item | Reason |
|---|---|
| Rework video pipeline | Current result is verified as ideal |
| Expand PTZ logic | Hardware-dependent and not core for release |
| Add more hidden hotkeys | Makes support harder |
| Add more raw sliders to context menu | Context menu must stay fast and simple |
| Store local runtime config as root `config.json` in repo | It is machine-specific state |

## Production candidate definition

The project can be tagged as production candidate when:

1. Known-good settings remain reproducible.
2. First launch can be configured without reading the source code.
3. README has launch/build instructions.
4. Legacy 11.5 files are absent from root.
5. Runtime log after a normal session has no traceback or ERROR.
6. The app starts, opens camera, starts virtual camera, switches camera, stops virtual camera, and exits cleanly on the target Windows machine.
