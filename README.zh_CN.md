# PDFCrop

PDFCrop 是一个用于学习的 PDF 文件查看器。它提供了将当前显示页面及其前几页提取为 PDF 文件并复制到剪贴板的功能。通过将其粘贴到 ChatGPT 等工具中，可以轻松地针对正在查看的页面提出具体问题。

![流程图](src/resources/flowdiagram.png)

## 功能

- 通过文件对话框、命令行或拖放打开 PDF。
- 支持页面滚动和缩放，窗口尺寸变化时自动按宽度适配。
- 非同步渲染和缓存机制带来更流畅的阅读体验。
- 按 `Ctrl+C`、右键单击或 Ctrl+左键单击，可将当前页及附近页作为新 PDF 复制到剪贴板，页数可在工具栏设置。
- 在查看区域右键拖动或按住Shift+左键拖动，可以截图并复制到剪贴板。
- 自动保存最近的文件、窗口位置、缩放倍率和语言设置。
- 支持的语言：英语、日语、简体中文、繁体中文。

## 安装

### Windows 用户

1. 从[发布页面](https://github.com/inoueakimitsu/pdfcrop/releases)下载最新的安装程序（PDFCrop_Setup.exe）
2. 运行安装程序并按照安装向导进行操作
3. 安装完成后可从开始菜单启动 PDFCrop

### 手动安装（适用于开发者）

1. 安装 Python 3.10 及以上版本
2. 安装依赖包：

   ```bash
   pip install PyMuPDF Pillow PySide6
   ```

3. 克隆本仓库后运行：

   ```bash
   python main.py path/to/file.pdf
   ```

## 使用方法

- **打开文件**：选择菜单 `File -> Open`，或将 PDF 拖入窗口，也可在命令行中直接指定路径。
- **页面操作**：使用鼠标滚轮、方向键或 PageUp/PageDown 进行滚动，`Home` 键回到首页，`End` 键到末尾。
- **复制页面**：按 `Ctrl+C`、右键单击或 Ctrl+左键单击，所选范围会作为 PDF 保存到剪贴板。
- **截图**：在页面上右键拖拽或按住Shift+左键拖拽即可选取区域，图像会存入剪贴板。
- **更改语言**：在 `Settings -> Language` 中选择，重启应用后生效。

## 许可证

本项目遵循 GNU AGPL v3 许可证，详情请参阅 `LICENSE` 文件。

贡献者和第三方库的许可信息见 `AUTHORS` 文件。
