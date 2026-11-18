---
name: swarm-video-skill
description: 将成片或剪辑工作区录屏做成多鼠标蜂群剪辑演示。彩色光标在左上选素材、左下点工具，再在下方时间线点击后铺开片段，支持右侧参数联动和可编辑 Remotion 工程。
---

# Swarm Video Skill

默认只需一条剪辑好的视频。成片放进播放器。左上素材、左下工作区、右侧参数和下方多轨时间线由不同光标分工。保留原生顶栏和中央预览画面。输出 MP4、可编辑 Remotion 工程和检查报告。

1. **生成前检查当前智能体的技能是否符合需求。** 运行 `python <技能目录>/scripts/check_skills.py --json`，阅读所需 Remotion 技能规则。缺失或不符合时先从官方来源安装相应技能并复查。核实本机有 Python 3.11+、Node.js 22.13+、FFmpeg 和 ffprobe。安装方式见 [前置检查](references/prerequisites.md)。
2. 对普通成片，运行 `python <技能目录>/scripts/run.py "成片.mp4"`。已配置的本机截图优先，未配置则使用内置剪辑模板。模板可选 `--template cut`、`--template composite`、`--template color`。默认原速、静音、60fps。要套本仓库的剪映界面，用 `--workspace-image docs/jianying-workspace.png --layout docs/jianying-layout.json`。
3. 自备截图用 `--workspace-image` 与 `--layout`。核对播放器、左上素材、左下工作区、右侧参数与时间线的位置，配置一次即可重复使用。见 [模板与录屏](references/layout.md)。
4. 已有工作区录屏用 `--recording`。先用 `--analyze-only` 查看抽帧和矩形，再用 `--layout` 校准播放器保护区和各面板。匹配仓库剪映截图的布局可直接传入 `docs/jianying-layout.json`。录屏默认 5 倍速、静音。
5. 核对 `checks/report.json` 与开头、中段、结尾的成片抽查图。左上素材卡片和左下工作区都应有光标移动、点击和对应反馈。各区域错开活动，验证一组「选素材 → 点工具 → 落片段」。时间线从空白逐步建立，片段在对应点击后出现。检查光标未遮挡中央播放器。交付 `swarm-video.mp4` 和 `project/`。

时间线、光标、波形和轨道是演示动画。播放器使用输入成片的画面，缩略图从同一条视频中抽取。处理细节见 [制作过程](references/production.md)，命令见 [README](README.md)。
