# 角色定妆、首帧和动作提示词

## 先固定能认出角色的细节

用一张双人定妆看相对身高、头身比例、服装和配饰。镜头需要转身时，再分别确认正面、侧面和背面。把真正需要跨镜头继承的特征写成短表。例如头发层次、镜腿位置、头纱固定点、捧花在哪只手、肩线与鞋底形状。用正面查辨识度，侧面查厚度和连接，背面查轮廓。

体素风用可见的材质描述。细小而有厚度的方块，台阶状边缘，略有倒角的块面，方块间有遮蔽阴影，柔光下轮廓仍清楚。近景中让脸、头发和衣服的块尺度相称。全景先保住人物轮廓，手部特写才需要更多局部细节。

沿用定妆图作为身份参考。上一镜末帧可用于约束下一镜的位置和视线，但要标明它提供的是姿态或布景。角色身份始终回到已确认的定妆图。每次只改一个影响验收的因素，例如镜腿、脚落点或手的位置，并逐项保留其他画面条件。 [OpenAI 图像提示词指南](https://developers.openai.com/api/docs/guides/image-prompting)

## GPT Image 首帧模板

> 图 1 是角色定妆，负责人物比例、发型和服装。图 2 是上一镜停稳时的画面，负责机位、左右位置和背景。生成一张 16:9 电影首帧。两名体素人物在灯笼石桥中央相对站稳，人物 A 左手拿花束，右手空着，人物 B 靠近桥中央的一侧手空着。前景能看见鞋底和石面。保留人物的圆眼镜、头纱固定点和原来的左右位置。细小实体方块，清楚的层叠轮廓和温暖逆光。画面中无文字和水印。

首帧验收时暂停放大。确认人物有空间完成下一动作，手脚起始位置合理，接触点和背景轴线清楚。若只拍雨滴等空镜，把可能被生成成人或道具的轮廓从首帧里移走。

## MiniMax H3 动作模板

> One continuous shot starting from the supplied image. The two characters take one short step toward each other and come to a stop. Both feet are planted on the stone at the end. The camera holds its side of the bridge and pushes in slightly. Keep their faces, voxel proportions, glasses and veil consistent. The bouquet stays in the same hand. No cuts or backward steps.

用动词交代一个可完成的动作，然后说明停止姿态、机位、需要保留的细节和常见误动作。让走近、停稳和握手分别占有清楚的起点和终点。后镜需要握手时，可以用已经站稳的画面做近景首帧。

对已经存在的参考图和成片，用新版本文件保留改动历史。只有用户的参考素材通过公开范围确认后，才把它加入公开样例。
