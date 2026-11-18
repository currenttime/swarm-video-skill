# 生成前先检查智能体技能

每次由智能体执行生成时，先检查现有技能**是否满足任务**，不能只检查 Python/npm 依赖，也不能因为技能目录存在就认定可用。

## 必要能力与默认技能

| 能力 | 默认检查技能 | 来源 |
|---|---|---|
| Remotion 工作流约束 | remotion-best-practices | remotion-dev/skills |
| 工程和 Composition 创建 | remotion-create | 同上 |
| 逐帧 React/SVG 动画 | remotion-markup | 同上 |
| 渲染与导出 | remotion-render | 同上 |

预览/用户要求打开工程时再检查 `remotion-studio`；修改可交互编辑界面时再检查 `remotion-interactivity`。本任务默认无字幕、无 BGM，不因技能列表丰富而安装无关技能。不需要 swarm-cursors 插件或剪映/AE/达芬奇专用自动化技能。

```bash
python /path/to/swarm-video-skill/scripts/check_skills.py --json
```

脚本在常见用户/项目技能目录查找可读 `SKILL.md`，核对名称和有效正文。非标准位置用多个 `--skill-root` 参数，或 `SKILL_ROOTS` 环境变量。托管/内置技能以智能体实际可用清单为准；脚本扫不到时，智能体核实并记录等价能力，不能误称已安装。

然后读取相关技能正文，确认不是空壳、缺页、只有不适用的产品能力，或引用了不存在的文件。旧版整合型 Remotion 技能若已包含上述完整规则，可由智能体认定等价，不必安装重复技能。`skills-check.json` 的文件可用检查与智能体的实际能力审查分别记录。

## 缺失或不符合：先安装，再复查

从官方来源安装所缺模块：

```bash
npx skills add remotion-dev/skills --skill remotion-best-practices remotion-create remotion-markup remotion-render -y
```

只缺一项时只安装那一项，例如：

```bash
npx skills add remotion-dev/skills --skill remotion-render -y
```

来源与目录已核实为：

- https://github.com/remotion-dev/skills
- `skills/remotion-best-practices/SKILL.md`
- `skills/remotion-create/SKILL.md`
- `skills/remotion-markup/SKILL.md`
- `skills/remotion-render/SKILL.md`

使用工具自带的技能安装器时，也可按这些路径安装。不要把 npm 包安装当成智能体技能安装。安装后重新检查；若智能体必须重新加载或开启新会话才能识别新技能，应明确告知并等待加载生效，不能继续假装已读取新技能。

当前执行环境允许安装、用户又已授权使用本技能完成视频时，在该授权范围内安装缺失项。受环境权限或网络限制时如实说明原因；不绕过安装限制，不静默改用不符合需求的工作流，不覆盖用户已有的自定义技能。

## 工具能力与运行环境

除了技能，还要检查读取本地文件、执行本地命令和写入输出目录的能力。默认成片模式使用已经标定的模板，直接按模板生成。更换截图或处理工作区录屏时，再用看图工具校准相应区域。

运行环境单独检查：Python 3.11+、Node.js 22.13+ 和 npm、FFmpeg/ffprobe、Python requirements。首次安装渲染依赖和浏览器需要网络。工具与环境都通过后才能运行完整生成。
