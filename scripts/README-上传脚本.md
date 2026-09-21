# 草稿箱上传脚本 · 配置说明

## 一次性准备（在微信公众平台后台操作）

1. 登录 [mp.weixin.qq.com](https://mp.weixin.qq.com)
2. 左下角「设置与开发」→「基本配置」
3. 复制 **AppID**（开发者ID，wx 开头）
4. 点「重置」生成 **AppSecret**（只显示一次，立即复制）
5. 在 **IP 白名单** 中添加当前出口 IP（运行脚本的机器公网 IP）

## 配置文件

复制 `config.example.json` 为 `config.json`，填入你的 AppID 和 AppSecret：

```json
{
  "appid": "wx1234567890abcdef",
  "appsecret": "你的AppSecret"
}
```

> ⚠️ `config.json` 包含敏感凭证，**不要提交到 Git**（已在 .gitignore 中排除）。

## 运行

```bash
python upload_to_draft.py \
    --config config.json \
    --title "文章标题" \
    --author "作者名" \
    --digest "文章摘要，不超过120字" \
    --content-html "./article.html" \
    --cover-image "./cover.png"
```

## 常见错误

| errcode | 含义 | 处理 |
|---|---|---|
| 40164 / 61004 | IP 不在白名单 | 把当前出口 IP 加入后台白名单 |
| 40001 | access_token 无效 | 检查 AppID/AppSecret，或稍后重试 |
| 40013 | AppID 无效 | 检查 config.json |
| 40125 | AppSecret 错误 | 重新在后台重置 AppSecret |
| 48002 | 接口权限不足 | 当前公众号类型不支持 draft/add |

## 红线

- **只上传草稿，绝不自动发布**
- 上传后必须人工在公众号后台检查排版、预览，确认后手动发布
