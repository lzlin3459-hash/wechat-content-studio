#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号草稿箱浏览器自动化上传脚本
流程：扫码登录 → 自动保存cookie → 自动上传标题/正文/封面 → 保存草稿

用法：
  第一次：python upload_browser.py --title "标题" --content-html "xxx.html" --cover-image "xxx.png"
  之后：自动用cookie登录，不用再扫码
"""

import argparse
import asyncio
import json
import os
from pathlib import Path

from playwright.async_api import async_playwright, Page, BrowserContext

# 配置
COOKIE_FILE = Path(__file__).parent / "wx_cookies.json"
HEADLESS = False  # 第一次扫码要显示浏览器，之后可以设为True
WECHAT_MP_URL = "https://mp.weixin.qq.com/"
DRAFT_URL = "https://mp.weixin.qq.com/cgi-bin/appmsg"


async def save_cookies(context: BrowserContext):
    """保存cookie到本地"""
    cookies = await context.cookies()
    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        json.dump(cookies, f, ensure_ascii=False, indent=2)
    print(f"[✓] Cookie 已保存到 {COOKIE_FILE}")


async def load_cookies(context: BrowserContext):
    """从本地加载cookie"""
    if not COOKIE_FILE.exists():
        print("[!] 没有找到cookie文件，需要重新扫码登录")
        return False
    with open(COOKIE_FILE, "r", encoding="utf-8") as f:
        cookies = json.load(f)
    await context.add_cookies(cookies)
    print(f"[✓] Cookie 已加载，共 {len(cookies)} 条")
    return True


async def login(page: Page):
    """登录：第一次扫码，之后自动登录"""
    print("[1/5] 打开微信公众号后台...")
    await page.goto(WECHAT_MP_URL, wait_until="domcontentloaded", timeout=60000)
    await asyncio.sleep(5)

    # 检查是否已经登录（cookie有效）
    if "cgi-bin/home" in page.url or "cgi-bin/dashboard" in page.url:
        print("[✓] Cookie有效，已自动登录")
        return True

    # 检查是否有登录二维码
    print("[!] 需要扫码登录，请用微信扫描浏览器中的二维码...")
    print("[!] 扫码后请等待自动跳转...")

    # 等待用户扫码登录（最多等60秒）
    try:
        await page.wait_for_url("**/cgi-bin/**", timeout=60000)
        print("[✓] 扫码成功，已登录")
        return True
    except Exception as e:
        print(f"[✗] 登录超时或失败：{e}")
        return False


async def upload_draft(page: Page, title: str, content_html_path: str, cover_image_path: str):
    """上传草稿：标题 + 正文 + 封面"""
    # 1. 进入新建图文页面
    print("[2/5] 进入新建图文页面...")
    await page.goto("https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit_v2&action=edit&isNew=1&type=77&token=&lang=zh_CN", wait_until="domcontentloaded", timeout=60000)
    await asyncio.sleep(5)

    # 2. 填入标题
    print("[3/5] 填入标题...")
    title_input = page.locator('textarea[placeholder="请输入标题（16-64字）"]').first
    await title_input.fill(title)
    print(f"  ✓ 标题：{title}")

    # 3. 填入正文HTML
    print("[4/5] 填入正文...")
    with open(content_html_path, "r", encoding="utf-8") as f:
        content_html = f.read()

    # 微信编辑器是 iframe，需要找到正文编辑器
    # 尝试多种选择器
    editor_frame = None
    for frame in page.frames:
        if "appmsg_edit" in frame.url or "ueditor" in frame.url.lower():
            editor_frame = frame
            break

    if editor_frame:
        # 用 JavaScript 设置 HTML
        await editor_frame.evaluate(f"""
            document.body.innerHTML = `{content_html.replace('`', '\\`')}`;
        """)
        print("  ✓ 正文已填入（通过iframe）")
    else:
        # 备用方案：直接用 contenteditable
        body_editor = page.locator('[contenteditable="true"]').first
        await body_editor.evaluate(f"el => el.innerHTML = `{content_html.replace('`', '\\`')}`")
        print("  ✓ 正文已填入（通过contenteditable）")

    await asyncio.sleep(1)

    # 4. 上传封面
    print("[5/5] 上传封面图...")
    # 找封面上传按钮
    cover_upload = page.locator('input[type="file"]').first
    await cover_upload.set_input_files(cover_image_path)
    await asyncio.sleep(3)  # 等待上传完成
    print(f"  ✓ 封面已上传：{os.path.basename(cover_image_path)}")

    # 5. 保存草稿
    print("[保存草稿] 点击保存...")
    save_btn = page.locator('button:has-text("保存为草稿")').first
    await save_btn.click()
    await asyncio.sleep(2)
    print("[✓] 草稿已保存！")

    # 截图保存结果
    screenshot_path = Path(__file__).parent / "upload_result.png"
    await page.screenshot(path=str(screenshot_path))
    print(f"[✓] 截图已保存到 {screenshot_path}")


async def main():
    parser = argparse.ArgumentParser(description="微信公众号草稿箱浏览器自动化上传")
    parser.add_argument("--title", required=True, help="文章标题")
    parser.add_argument("--content-html", required=True, help="正文 HTML 文件路径")
    parser.add_argument("--cover-image", required=True, help="封面图路径")
    args = parser.parse_args()

    # 检查文件是否存在
    if not os.path.exists(args.content_html):
        print(f"[ERROR] 正文文件不存在：{args.content_html}")
        return
    if not os.path.exists(args.cover_image):
        print(f"[ERROR] 封面文件不存在：{args.cover_image}")
        return

    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=HEADLESS)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        page = await context.new_page()

        # 尝试加载cookie
        cookie_loaded = await load_cookies(context)
        if cookie_loaded:
            await page.goto(WECHAT_MP_URL, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(5)
            # 检查cookie是否有效
            if "cgi-bin/home" in page.url or "cgi-bin/dashboard" in page.url:
                print("[✓] Cookie有效，已自动登录")
            else:
                print("[!] Cookie已过期，需要重新扫码")
                cookie_loaded = False

        # 如果cookie无效，需要扫码登录
        if not cookie_loaded:
            success = await login(page)
            if not success:
                print("[ERROR] 登录失败")
                await browser.close()
                return
            # 登录成功后保存cookie
            await save_cookies(context)

        # 上传草稿
        try:
            await upload_draft(page, args.title, args.content_html, args.cover_image)
            print("\n[✓✓✓] 上传完成！请去公众号草稿箱检查。")
        except Exception as e:
            print(f"[ERROR] 上传失败：{e}")
            import traceback
            traceback.print_exc()
        finally:
            await asyncio.sleep(5)  # 等一下让用户看到结果
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
