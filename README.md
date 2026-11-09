# H3 × GPT Image MV Skill

Build a music video from GPT Image keyframes and MiniMax H3 shots in ComfyUI. The skill covers character consistency, shot continuity, and frame-accurate 1080p assembly, with examples for a 15-second voxel short.

从角色定妆、分镜首帧到 H3 图生视频，再按音乐完成剪辑。也可以从已有素材开始，只修动作回跳、接缝或时长问题。

## 安装

把这个仓库放进 Codex 可发现的 Skills 目录。以下是 macOS / Linux 的用户级安装示例。已有同名 Skill 时，先检查已安装的位置再更新那一份。 [Codex Skills 文档](https://learn.chatgpt.com/docs/build-skills#where-to-save-skills)

```bash
mkdir -p "$HOME/.agents/skills"
git clone https://github.com/ZSeven-W/h3-gpt-image-mv.git "$HOME/.agents/skills/h3-gpt-image-mv"
```

在 Codex 输入下面这句，附上已有素材和交付需求。

> 用 $h3-gpt-image-mv 做一支 15 秒的体素短片。角色参考和配乐在当前项目里。先设计三个能接起来的镜头，确认其中最难的一镜能出片，再继续生成。

使用已有 ComfyUI 的 H3 I2V 模板生成片段。合片脚本需要 Python 3.10+、FFmpeg 与 FFprobe，以及支持硬链接的本地输出目录。可按环境选择可用的 GPT Image 入口。 [ComfyUI H3 工作流](https://docs.comfy.org/tutorials/video/minimax/minimax-h3-native)

## 先做 15 秒样片

1. 把 [示例清单](assets/timeline.example.json) 复制到你的项目。用 [定妆与提示词](references/keyframes.md) 准备三张首帧。
2. 按 [H3 试跑与配置](references/comfyui.md) 生成三条 24 fps 源片。示例为每条生成 124 帧，剪辑取前 120 帧。
3. 把源片与 15 秒 AAC 配乐放在清单指定位置，再用 [合片与验收说明](references/editing.md) 检查和导出。清单内的相对路径以清单所在目录为准。

```bash
python3 "$HOME/.agents/skills/h3-gpt-image-mv/scripts/assemble.py" timeline.json --check
python3 "$HOME/.agents/skills/h3-gpt-image-mv/scripts/assemble.py" timeline.json --output mv.mp4
```

合片脚本处理 1920 × 1080 或 1920 × 1088 的 24 fps 素材。1920 × 1088 会对称裁掉上下各 4 像素。脚本按帧取片、验证 MP4 时间戳和 AAC 数据，在通过完整解码检查后写入输出文件。需要变速、补帧、字幕或叠化时，在剪辑器里先渲染该段，再放入清单。

[SKILL.md](SKILL.md) 是给 agent 的入口。仓库示例使用虚构场景，模型和模板从各自发布方获取。

## License

[MIT](LICENSE)
