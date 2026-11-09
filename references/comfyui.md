# MiniMax H3 与 ComfyUI

## 先跑通一条

1. 打开已配置的 ComfyUI。搜索 **MiniMax H3 Image to Video**，或导入与本机安装相匹配的官方 I2V 模板。按模板缺失模型提示核对 checkpoint、文本编码器、VAE 和对应 Turbo LoRA。把模板导出到项目，记录 ComfyUI 和模板版本。 [ComfyUI 原生 H3 教程](https://docs.comfy.org/tutorials/video/minimax/minimax-h3-native)
2. 让 `Load Image` 接入 `first_frame`，再把 I2V 输出接到 `SaveVideo`。固定同镜头的 seed 做比较。先用预设尺寸生成约 5 秒的测试件，核验模型能加载、MP4 能保存，以及人物和动作成立。再将同一镜头提升到交付尺寸测显存、耗时和有效帧数。
3. 提示词依次写连续单镜头、动作和落点、运镜、角色不变量及禁用动作。首帧先满足这些约束。例如两位虚构角色牵手走上一级台阶并站定，左右位置不换，脚接触石面，镜头沿同一轴线缓慢拉远。`last_frame` 仅在确实要约束终点时连接。需要持续推进时，避免把起点又接成终点。
4. 成片只用独立配乐时，可以在 API 工作流断开 `CreateVideo` 的音频输入，移除已无调用的音频解码节点。若保留工坊图中的音频支路，合成时仅映射 H3 的视频流。 [MiniMax H3 模型介绍](https://www.minimax.io/blog/minimax-h3)

## 1080p 实测参数

以下是一套 Windows + NVIDIA 工坊预设的实测变体。这套参数来自一次成片制作。其他版本的默认尺寸、VAE、精度和步数可能不同，官方教程也包含 1344 × 768 的工作流。复刻时先在本机试跑单条，以原始产物确认实际尺寸。

| 项目 | 该案例值 |
| --- | --- |
| I2V 节点 | `MiniMaxH3ImageToVideo`，连接首帧 |
| Diffusion model | `minimax_h3_fl2va_pruned_int8_convrot.safetensors` |
| Text encoder | `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`，类型 `minimax` |
| 视频 VAE | `minimax_h3_video_vae_fp16.safetensors` |
| LoRA | `minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors`，强度 1 |
| Sampler | `res_multistep` |
| Scheduler | `simple`，实际采样 8 步，denoise 1 |
| 生成尺寸 | 1920 × 1088，24 fps，最后上下各裁 4 px |
| 常用生成帧数 | 124 / 141 / 158 / 175，按需剪短 |

UI 用显式宽高时，要检查子图的宽高是否仍被外部 `ResolutionSelector` 或 `GetImageSize` 连线覆盖。案例断开覆盖连线后写入宽高。Turbo 分支可能覆盖基础节点 widget 中显示的步数，以实际接入采样链的节点为准。 [ComfyUI 官方工作流 JSON](https://github.com/Comfy-Org/workflow_templates/blob/main/templates/video_minimax_h3_i2v.json)

此预设将秒换算成 24 fps 帧数，再上取整到 `17k + 5`。API 直接写整数 `length` 时，若需要保留 `T` 个源帧，可用 `5 + 17 × ceil(max(0, T - 5) / 17)` 找到足够的合法长度，并确认未超过当前模板与设备的限制。若要裁头，先将裁掉的源帧计入 `T`。例如保留 120 帧，从首帧开始剪，生成 124 帧。

## 批量与断点恢复

单卡先串行跑短批次，记录首条真实完成时间后再估算全批耗时。处理掉线、显存不足或散热暂停时，保留已确认的输出。需要提速时先用同种子、同分辨率的短镜头比较时间与画面，再决定是否换采样或注意力路径。

- 优先复用已有 runner 或从运行正常的 UI 导出 **API 格式**，用稳定的节点类型和连接识别字段。界面工作流 JSON 与 `/prompt` 的 API 图结构不同，节点编号也因模板而异。
- 先 `POST /upload/image`，把返回的文件名与子目录填入 `LoadImage`。每个镜头单独 `POST /prompt`，把 `prompt_id`、输入图指纹、种子、尺寸、版本和预期输出写入本地任务记录。用 `GET /queue` 与 `GET /history/{prompt_id}` 区分运行、完成和失败。客户端超时后先查已有记录和服务器队列；确认旧任务已失败或已取消后再提交新版本。
- 从历史的实际输出描述取 `filename`、`subfolder` 和 `type`，经 `GET /view` 下载到临时文件。用 `ffprobe` 确认尺寸、帧率与帧数，再移动到正式目录。修改提示或首帧后另存 `shot-v2`，保留已通过的上一版。 [ComfyUI Server Routes](https://docs.comfy.org/development/comfyui-server/comms_routes)
- 若客户端在同一个可信局域网，用用户提供的地址。先做只读连通检查。环境代理拦截局域网时，对该次请求使用目标主机的代理豁免。发布教程或分享工作流时，替换个人服务器地址、输入图片名和路径。
