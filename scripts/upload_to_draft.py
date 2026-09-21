#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号草稿箱上传脚本
流程：获取 access_token → 上传封面永久素材 → draft/add 写入草稿箱

用法：
  python upload_to_draft.py --config config.json \
      --title "文章标题" --author "作者" --digest "摘要" \
      --content-html "./article.html" --cover-image "./cover.png"

仅上传草稿箱，绝不自动发布。上传后请在公众号后台人工检查并确认。
"""

import argparse
import json
import mimetypes
import os
import sys
import urllib.request
import urllib.parse
import uuid

TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
MATERIAL_ADD_URL = "https://api.weixin.qq.com/cgi-bin/material/add_material"
DRAFT_ADD_URL = "https://api.weixin.qq.com/cgi-bin/draft/add"

ERROR_HINTS = {
    40164: "当前 IP 不在白名单。请在公众号后台「设置与开发→基本配置→IP白名单」添加当前出口 IP。",
    61004: "当前 IP 不在白名单（同 40164）。请检查 IP 白名单配置。",
    40001: "access_token 无效或已过期。请检查 AppID/AppSecret 是否正确，或稍后重试。",
    40013: "AppID 无效。请检查 config.json 中的 appid。",
    40125: "AppSecret 错误。请检查 config.json 中的 appsecret。",
    48002: "接口权限不足。当前公众号类型不支持该接口（draft/add）。",
}


def http_get_json(url):
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_post_json(url, payload):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_post_multipart(url, file_path):
    """手动构造 multipart/form-data 上传文件（不依赖 requests）"""
    boundary = "----WebKitFormBoundary" + uuid.uuid4().hex
    filename = os.path.basename(file_path)
    with open(file_path, "rb") as f:
        file_bytes = f.read()
    mime = mimetypes.guess_type(filename)[0] or "application/octet-stream"

    body = b""
    body += f"--{boundary}\r\n".encode()
    body += f'Content-Disposition: form-data; name="media"; filename="{filename}"\r\n'.encode("utf-8")
    body += f"Content-Type: {mime}\r\n\r\n".encode()
    body += file_bytes + b"\r\n"
    body += f"--{boundary}--\r\n".encode()

    req = urllib.request.Request(url, data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def check_error(resp, step):
    errcode = resp.get("errcode", 0)
    if errcode != 0:
        hint = ERROR_HINTS.get(errcode, resp.get("errmsg", "未知错误"))
        print(f"[ERROR] {step} 失败：errcode={errcode}，{hint}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="上传图文到微信公众号草稿箱")
    parser.add_argument("--config", required=True, help="配置文件路径（含 appid/appsecret）")
    parser.add_argument("--title", required=True, help="文章标题")
    parser.add_argument("--author", required=True, help="作者")
    parser.add_argument("--digest", required=True, help="摘要（不超过120字）")
    parser.add_argument("--content-html", required=True, help="正文 HTML 文件路径")
    parser.add_argument("--cover-image", required=True, help="封面图路径（jpg/png）")
    parser.add_argument("--content-source-url", default="", help="原文链接（可选）")
    args = parser.parse_args()

    # 1. 读配置
    with open(args.config, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    appid = cfg["appid"]
    appsecret = cfg["appsecret"]

    # 2. 获取 access_token
    print("[1/4] 获取 access_token ...")
    token_resp = http_get_json(f"{TOKEN_URL}?grant_type=client_credential&appid={appid}&secret={appsecret}")
    check_error(token_resp, "获取 access_token")
    token = token_resp["access_token"]
    print(f"      ✓ token 获取成功（有效期 {token_resp.get('expires_in', 7200)} 秒）")

    # 3. 上传封面为永久素材
    print("[2/4] 上传封面图 ...")
    material_resp = http_post_multipart(f"{MATERIAL_ADD_URL}?access_token={token}&type=image", args.cover_image)
    check_error(material_resp, "上传封面素材")
    thumb_media_id = material_resp["media_id"]
    print(f"      ✓ 封面上传成功，thumb_media_id={thumb_media_id}")

    # 4. 读正文 HTML
    print("[3/4] 读取正文 HTML ...")
    with open(args.content_html, "r", encoding="utf-8") as f:
        content_html = f.read()
    print(f"      ✓ 正文 {len(content_html)} 字符")

    # 5. 写入草稿箱
    print("[4/4] 写入草稿箱 ...")
    article = {
        "title": args.title,
        "author": args.author,
        "digest": args.digest,
        "content": content_html,
        "content_source_url": args.content_source_url,
        "thumb_media_id": thumb_media_id,
        "need_open_comment": 0,
        "only_fans_can_comment": 0,
    }
    draft_resp = http_post_json(f"{DRAFT_ADD_URL}?access_token={token}", {"articles": [article]})
    check_error(draft_resp, "写入草稿箱")
    media_id = draft_resp["media_id"]
    print(f"      ✓ 草稿已写入！草稿 media_id={media_id}")
    print()
    print("【下一步】请登录微信公众平台 → 草稿箱，检查排版、预览后人工确认发布。")


if __name__ == "__main__":
    main()
