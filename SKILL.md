---
name: swarm-video-skill
description: 将一条剪辑好的成片放进静态剪辑工作区，自动生成多光标协作、点选后逐步出现的多轨时间线和可编辑 Remotion 工程。也支持给已有工作区录屏叠加同款时间线动效。
---

# Swarm Video Skill

默认只需一条剪辑好的视频。把视频完整放进静态工作区的播放器，下方多光标依次点击并建立时间线。输出 MP4、可编辑 Remotion 工程和检查报告。

1. **生成前检查当前智能体的技能是否符合需求。** 运行 `python <技能目录>/scripts/check_skills.py --json`，阅读所需 Remotion 技能规则。缺失或不符合时先从官方来源安装相应技能并复查。核实本机有 Python 3.11+、Node.js 22.13+、FFmpeg 和 ffprobe。安装方式见 [前置检查](references/prerequisites.md)。
2. 对普通成片，运行 `python <技能目录>/scripts/run.py "成片.mp4"`。已配置的本机截图优先，未配置则使用内置剪辑模板。用户指定模板风格时可用 `--template cut`、`--template composite` 或 `--template color` 选择。默认原速、静音、60fps，可按要求加速。成片模式直接使用模板已标定的播放器和时间线区域。
3. 有用户自备的剪辑软件截图时，在图上确定播放器和时间线矩形，再调用 `--workspace-image` 与 `--layout`。常用截图配置一次即可，日常只需给视频。格式见 [模板与录屏](references/layout.md)。
4. 如果用户明确提供的是工作区录屏并要求保留画面，用 `--recording`。这一模式先用 `--analyze-only` 查看抽帧和矩形，再用 `--layout` 校准后渲染。录屏模式默认 5 倍速。
5. 核对 `checks/report.json` 和成片抽查图，确认视频在播放器内，背景固定且光标只出现在时间线，片段随点击逐步出现。交付 `swarm-video.mp4` 和 `project/`。

时间线、光标、波形和轨道是演示动画。播放器使用输入成片的画面，缩略图从同一条视频中抽取。处理细节见 [制作过程](references/production.md)，命令见 [README](README.md)。
