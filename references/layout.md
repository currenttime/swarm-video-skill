# 静态模板与工作区录屏

## 使用自己的界面截图

选取一张固定的剪映、After Effects 或 DaVinci Resolve 工作区截图，确定播放器内容区和下方时间线区。坐标用截图的宽高归一化到 0..1。播放器与时间线需互不重叠，时间线区域至少占画面宽度的 40%、高度的 16%。

```json
{
  "player": {"x": 0.35, "y": 0.12, "width": 0.35, "height": 0.37},
  "timeline": {"x": 0, "y": 0.61, "width": 1, "height": 0.39}
}
```

指定截图和坐标即可使用。尺寸和坐标以实际截图为准。

```bash
python scripts/run.py "成片.mp4" --workspace-image "workspace.png" --layout "layout.json"
```

如果要长期使用同一截图，把截图与 `workspace.json` 放在 `~/.config/swarm-video-skill/`。例如 `workspace.json` 内容如下。

```json
{
  "image": "workspace.png",
  "layout": {
    "player": {"x": 0.35, "y": 0.12, "width": 0.35, "height": 0.37},
    "timeline": {"x": 0, "y": 0.61, "width": 1, "height": 0.39}
  }
}
```

之后直接运行 `python scripts/run.py "成片.mp4"`。显式指定 `--template` 或 `--workspace-image` 可覆盖本地默认图。截图外的面板保持静态，播放器使用等比缩放补边。透明光标和时间线动效统一限制在时间线区域内。

## 继续使用录屏模式

```bash
python scripts/run.py "工作区录屏.mp4" --recording --analyze-only --output "分析目录"
python scripts/run.py "工作区录屏.mp4" --recording --layout "录屏布局.json" --output "输出目录"
```

在 `checks/source-0.jpg` 到 `source-2.jpg` 中定位实际时间线，再核对 `layout.jpg`。选定矩形包括时间线工具栏、刻度和所有轨道。录屏模式的布局只写 `timeline`，可额外写 `thumbnail` 指定缩略图来源。如果录屏切换了工作区，需要按界面固定的区间分段。
