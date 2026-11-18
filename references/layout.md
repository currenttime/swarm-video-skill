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

之后直接运行 `python scripts/run.py "成片.mp4"`。显式指定 `--template` 或 `--workspace-image` 可覆盖本地默认图。播放器使用等比缩放补边。

可以在同一布局里用 `media`（左上素材区）、`controls`（左下工作区）、`inspector`（右侧参数）和 `transport`（播放器下方控制区）指定面板矩形。旧配置会依据播放器和时间线之间的空间补齐可用区域。各区域互不重叠，顶栏和播放器留在动画区域之外。精确坐标示例见 [剪映布局](../docs/jianying-layout.json)。

## 继续使用录屏模式

```bash
python scripts/run.py "工作区录屏.mp4" --recording --analyze-only --output "分析目录"
python scripts/run.py "工作区录屏.mp4" --recording --layout "录屏布局.json" --output "输出目录"
```

在 `checks/source-0.jpg` 到 `source-2.jpg` 中定位实际时间线、播放器和面板，再核对 `layout.jpg`。时间线矩形包括工具栏、刻度和所有轨道。用 `player` 或 `preview` 标注播放器保护区域，使用 `thumbnail` 可另行指定缩略图来源。缺少播放器坐标时，自动布局仅在左侧留出较窄的操作区；预览或面板位置特殊时应手动校准。录屏切换了工作区时，按界面固定的区间分段。
