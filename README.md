# H3 × GPT Image MV Skill

Build a music video from GPT Image keyframes and MiniMax H3 shots in ComfyUI. The skill covers character consistency, shot continuity, and frame-accurate 1080p assembly, with examples for a 15-second voxel short.

从角色定妆、分镜首帧到 H3 图生视频，再按音乐完成剪辑。也可以从已有素材开始，只修动作回跳、接缝或时长问题。

## 安装

在项目目录用 `npx skills` 安装。下面这条命令为 Claude Code、Cursor 和 Codex 安装同一份 Skill。只用其中一个客户端时，在 `-a` 后保留它的标识。添加 `-g` 可安装到用户目录。 [Skills CLI 文档](https://github.com/vercel-labs/skills/blob/main/docs/commands.md#skills-add)

```bash
npx skills add ZSeven-W/h3-gpt-image-mv --skill h3-gpt-image-mv -a claude-code cursor codex
```

也可以用 Git 手动安装。把仓库完整克隆为下表任一技能目录下的 `h3-gpt-image-mv`，保留 `SKILL.md`、`assets/`、`references/` 和 `scripts/` 的相对位置。

| 客户端 | `-a` 标识 | 手动安装目录（项目 / 用户） | 文档 |
| --- | --- | --- | --- |
| Claude Code | `claude-code` | `.claude/skills/` / `~/.claude/skills/` | [Claude Code](https://code.claude.com/docs/en/skills) |
| Cursor | `cursor` | `.agents/skills/` / `~/.agents/skills/` | [Cursor](https://cursor.com/docs/skills) |
| Codex | `codex` | `.agents/skills/` / `~/.agents/skills/` | [Codex](https://learn.chatgpt.com/docs/build-skills#where-to-save-skills) |
| OpenCode | `opencode` | `.agents/skills/` / `~/.agents/skills/` | [OpenCode](https://opencode.ai/docs/skills/#discovery) |
| Gemini CLI | `gemini-cli` | `.agents/skills/` / `~/.agents/skills/` | [Gemini CLI](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/skills.md#discovery-tiers) |
| GitHub Copilot | `github-copilot` | `.agents/skills/` / `~/.agents/skills/` | [GitHub Copilot](https://docs.github.com/en/copilot/concepts/customizations/agent-skills#finding-and-storing-skills) |

例如，用 Git 把 Skill 装进当前项目的 Claude Code 技能目录。

```bash
mkdir -p .claude/skills
git clone https://github.com/ZSeven-W/h3-gpt-image-mv.git .claude/skills/h3-gpt-image-mv
```

在客户端里通过名字调用 Skill，并附上已有素材和交付需求。Claude Code 和 Cursor 可以用 `/h3-gpt-image-mv`，Codex 可以用 `$h3-gpt-image-mv`。

> 使用 h3-gpt-image-mv Skill 做一支 15 秒的体素短片。角色参考和配乐在当前项目里。先设计三个能接起来的镜头，确认其中最难的一镜能出片，再继续生成。

使用已有 ComfyUI 的 H3 I2V 模板生成片段。合片脚本需要 Python 3.10+、FFmpeg 与 FFprobe，以及支持硬链接的本地输出目录。可按环境选择可用的 GPT Image 入口。 [ComfyUI H3 工作流](https://docs.comfy.org/tutorials/video/minimax/minimax-h3-native)

## 先做 15 秒样片

1. 把 [示例清单](assets/timeline.example.json) 复制到你的项目。用 [定妆与提示词](references/keyframes.md) 准备三张首帧。
2. 按 [H3 试跑与配置](references/comfyui.md) 生成三条 24 fps 源片。示例为每条生成 124 帧，剪辑取前 120 帧。
3. 把源片与 15 秒 AAC 配乐放在清单指定位置，再用 [合片与验收说明](references/editing.md) 检查和导出。清单内的相对路径以清单所在目录为准。

用上面的 `npx` 命令安装到当前项目时，脚本在 `.agents/skills/`。用 Git 安装时，从克隆的目录取脚本路径。

```bash
python3 .agents/skills/h3-gpt-image-mv/scripts/assemble.py timeline.json --check
python3 .agents/skills/h3-gpt-image-mv/scripts/assemble.py timeline.json --output mv.mp4
```

合片脚本处理 1920 × 1080 或 1920 × 1088 的 24 fps 素材。1920 × 1088 会对称裁掉上下各 4 像素。脚本按帧取片、验证 MP4 时间戳和 AAC 数据，在通过完整解码检查后写入输出文件。需要变速、补帧、字幕或叠化时，在剪辑器里先渲染该段，再放入清单。

[SKILL.md](SKILL.md) 是给 agent 的入口。仓库示例使用虚构场景，模型和模板从各自发布方获取。

## License

[MIT](LICENSE)
