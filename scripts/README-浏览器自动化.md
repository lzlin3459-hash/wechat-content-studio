# 浏览器自动化上传脚本 · 说明

## 为什么要有这个？

API 方式上传草稿箱需要：
- 配置 AppID / AppSecret
- 配置 IP 白名单
- 处理动态 IP 问题

**浏览器自动化方式**：扫码登录一次，以后自动用 cookie 登录，不需要管这些。

---

## 使用方法

### 第一次：扫码登录

```bash
python upload_browser.py --title "文章标题" --content-html "xxx.html" --cover-image "xxx.png"
```

1. 浏览器会自动打开微信公众号后台
2. 用微信扫码登录
3. 登录成功后 cookie 会自动保存到本地（`wx_cookies.json`）

### 之后：自动上传

```bash
python upload_browser.py --title "文章标题" --content-html "xxx.html" --cover-image "xxx.png"
```

- 自动用保存的 cookie 登录
- 自动填入标题、正文、封面
- 自动保存草稿

---

## 脚本流程

```
1. 打开微信公众号后台
   ↓
2. 检查 cookie 是否有效
   ├─ 有效 → 直接进入后台
   └─ 无效 → 显示二维码，等待扫码
   ↓
3. 进入新建图文页面
   ↓
4. 填入标题
   ↓
5. 填入正文 HTML
   ↓
6. 上传封面图
   ↓
7. 点击保存草稿
```

---

## 文件说明

| 文件 | 说明 |
|---|---|
| `upload_browser.py` | 浏览器自动化上传脚本 |
| `wx_cookies.json` | 保存的登录 cookie（自动生成） |
| `upload_result.png` | 上传结果截图（自动生成） |

---

## 注意事项

- **cookie 有效期**：一般 1-2 周，过期后需要重新扫码
- **headless 模式**：第一次扫码要显示浏览器（`HEADLESS = False`），之后可以改成 `True` 后台运行
- **不要上传到 GitHub**：`wx_cookies.json` 包含登录凭证，已在 .gitignore 中排除

---

## 与 API 方式对比

| 对比项 | API 方式 | 浏览器自动化 |
|---|---|---|
| 配置复杂度 | 高（AppID/Secret/白名单） | 低（扫码一次） |
| IP 问题 | 有（动态IP麻烦） | 无 |
| 稳定性 | 高 | 中（cookie过期要重扫） |
| 速度 | 快 | 慢（要打开浏览器） |
| 适合场景 | 服务器/自动化 | 本地/个人使用 |
