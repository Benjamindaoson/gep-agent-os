"""Render MOVA site on real desktop and tablet viewports.

Run via Python Playwright after launching a local server:
  python -m http.server 8766 --directory site
  python scripts/visual_smoke_site.py

A desktop screenshot artifact makes layout regressions inspectable.
"""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE=os.environ.get("SITE_URL","http://127.0.0.1:8766/")
OUTPUT=Path(os.environ.get("SITE_SCREENSHOTS","site-screenshots"))
OUTPUT.mkdir(parents=True,exist_ok=True)
VIEWPORTS=[("desktop-1440",1440,900),("desktop-1280",1280,900),
           ("desktop-1024",1024,768),("tablet-768",768,1024),
           ("phone-390",390,844)]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    for label,width,height in VIEWPORTS:
        page=browser.new_page(viewport={"width":width,"height":height},device_scale_factor=1)
        errors=[]
        page.on("pageerror",lambda error:errors.append(str(error)))
        response=page.goto(BASE,wait_until="networkidle",timeout=30000)
        assert response and response.status==200,(label,"site status")
        page.screenshot(path=str(OUTPUT/f"{label}.png"),full_page=True,animations="disabled")
        result=page.evaluate("""() => {
          const hero=document.querySelector('.hero');
          const title=document.querySelector('.hero h1');
          const card=document.querySelector('.demo-app');
          const css=[...document.styleSheets].map(x=>x.href||'').filter(Boolean);
          const elementRect=x=>({width:x.getBoundingClientRect().width,
              height:x.getBoundingClientRect().height,
              left:x.getBoundingClientRect().left,
              right:x.getBoundingClientRect().right});
          return {background:getComputedStyle(document.body).backgroundColor,
            grid:getComputedStyle(hero).display,title:elementRect(title),
            card:elementRect(card),documentWidth:document.documentElement.scrollWidth,
            windowWidth:window.innerWidth,text:document.body.innerText,
            cssUrls:css};
        }""")
        assert result["background"]=="rgb(8, 14, 28)",(label,"CSS not loaded",result["background"])
        assert result["grid"]=="grid",(label,"hero not grid")
        assert result["title"]["width"]>150 and result["card"]["width"]>200,(label,"collapsed content")
        assert result["documentWidth"]<=width+4,(label,"horizontal overflow",result["documentWidth"],width)
        assert "成为 AI Agent 工程师" in result["text"],(label,"target message missing")
        assert "不只是 AI 助手" in result["text"],(label,"hero missing")
        assert "�" not in result["text"],(label,"invalid UTF-8 replacement character")
        assert any("?v=20261010b" in url for url in result["cssUrls"]),(label,"cache busting absent")
        assert not errors,(label,"runtime script errors",errors)
        print(f"PASS {label}: {width}x{height} / CSS loaded / no overflow / valid text")
        page.close()
    browser.close()
