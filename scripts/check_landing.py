#!/usr/bin/env python3
"""Verifica la landing original: quickstart, meta, stats y playground.

Recorre la página antes de capturar para disparar los reveal y evitar
artefactos de position:sticky en las capturas full-page.
"""
import os
from playwright.sync_api import sync_playwright

BASE = 'http://localhost:8080'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = os.path.join(ROOT, 'api', 'temp', '_shots')
os.makedirs(SHOTS, exist_ok=True)


def settle(page):
    height = page.evaluate('document.body.scrollHeight')
    step = 600
    pos = 0
    while pos < height:
        page.evaluate(f'window.scrollTo(0, {pos})')
        page.wait_for_timeout(140)
        pos += step
        height = page.evaluate('document.body.scrollHeight')
    page.evaluate('window.scrollTo(0, 0)')
    page.wait_for_timeout(500)


def run(browser, version, sel_status='#pg-status', sel_out='#pg-output'):
    ctx = browser.new_context(viewport={'width': 1440, 'height': 960})
    page = ctx.new_page()
    errs = []
    page.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
    page.on('pageerror', lambda e: errs.append(str(e)))

    page.goto(f'{BASE}/{version}', wait_until='networkidle')
    page.wait_for_timeout(1200)
    settle(page)

    print(f'\n=== {version} ===')
    print('canonical :', page.get_attribute('link[rel=canonical]', 'href'))
    print('og:url    :', page.get_attribute('meta[property="og:url"]', 'content'))
    print('actualiz. :', (page.text_content('#foot-update') or '').strip())
    print('ipc hint  :', (page.text_content('#stat-ipc-hint') or '').strip())
    print('stats     :', [(page.text_content(f'#{i}') or '').strip() for i in
                          ('stat-ipc', 'stat-cba', 'stat-emae', 'stat-ica')])

    if version == 'index.html':
        print('\n-- quickstart --')
        print('curl  :', (page.text_content('#qs-code') or '').strip()[:60])
        page.click('.qs-tab[data-lang="py"]')
        page.wait_for_timeout(250)
        print('py    :', (page.text_content('#qs-code') or '').strip()[:60].replace('\n', ' '))
        page.click('.qs-tab[data-lang="js"]')
        page.wait_for_timeout(250)
        print('js    :', (page.text_content('#qs-code') or '').strip()[:60].replace('\n', ' '))

    print('\n-- playground --')
    page.select_option('#pg-ind', 'ipc')
    page.wait_for_timeout(900)
    f1 = page.eval_on_selector_all('#pg-f1 option', 'e=>e.map(x=>x.value).filter(Boolean)')
    print('f1    :', f1)
    page.select_option('#pg-f1', 'Nacional')
    page.wait_for_timeout(500)
    f2 = page.eval_on_selector_all('#pg-f2 option', 'e=>e.map(x=>x.value).filter(Boolean)')
    print('f2    :', f2)
    page.click('#pg-run')
    page.wait_for_timeout(1400)
    print('status:', (page.text_content(sel_status) or '').strip())

    doc_rows = page.eval_on_selector_all('.doc-row', 'e=>e.length')
    print('doc rows visibles:', doc_rows)

    real = [e for e in errs if 'cloudflareinsights' not in e and 'ERR_FAILED' not in e]
    print('errores consola:', real or 'ninguno')

    page.screenshot(path=f'{SHOTS}/landing-desktop.png', full_page=True)
    page.set_viewport_size({'width': 390, 'height': 844})
    page.wait_for_timeout(700)
    settle(page)
    page.screenshot(path=f'{SHOTS}/landing-mobile.png', full_page=True)
    ctx.close()
    return real


if __name__ == '__main__':
    with sync_playwright() as p:
        b = p.chromium.launch()
        problems = run(b, 'index.html')
        b.close()
    raise SystemExit(1 if problems else 0)
