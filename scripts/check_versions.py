#!/usr/bin/env python3
"""Verifica en navegador real: filtros, stats y playground de cada version.

Uso:  python3 scripts/check_versions.py [version-b ...]
"""
import sys
import os
from playwright.sync_api import sync_playwright

BASE = 'http://localhost:8080/temp'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = os.path.join(ROOT, 'api', 'temp', '_shots')

# selectores de stats por version: (contenedor, valor, meta)
STATS = {
    'version-a': ('#stat-ipc', '#stat-cba', '#stat-emae', '#stat-ica'),
    'version-b': ('#hs-ipc .hs-val', '#hs-cba .hs-val', '#hs-emae .hs-val', '#hs-ica .hs-val'),
    'version-c': ('#d-ipc .datum-val', '#d-cba .datum-val', '#d-emae .datum-val', '#d-ica .datum-val'),
    'version-d': ('#stat-ipc', '#stat-cba', '#stat-emae', '#stat-ica'),
    'version-e': ('#stat-ipc', '#stat-cba', '#stat-emae', '#stat-ica'),
    'version-f': ('#stat-ipc', '#stat-cba', '#stat-emae', '#stat-ica'),
}
OUT = {'version-a': '#pg-output', 'version-b': '#pg-output', 'version-c': '#pg-output', 'version-d': '#pg-output', 'version-e': '#pg-output', 'version-f': '#pg-output'}
STATUS = {'version-a': '#pg-status', 'version-b': '#pg-status', 'version-c': '#pg-status', 'version-d': '#pg-status', 'version-e': '#pg-status', 'version-f': '#pg-status'}


def opts(page, sel):
    return page.eval_on_selector_all(
        f'{sel} option', 'els => els.map(e => e.value).filter(Boolean)'
    )


def check(version, page, errors):
    print(f'\n=== {version} ===')
    page.goto(f'{BASE}/{version}/index.html', wait_until='networkidle')
    page.wait_for_timeout(1200)

    # 1) stats cargadas
    print('  stats:', end=' ')
    for sel in STATS[version]:
        t = (page.text_content(sel) or '').strip()
        print(f'{t!r}', end=' ')
    print()

    # 2) primer filtro (debe ser región para ipc)
    f1 = opts(page, '#pg-f1')
    print('  f1 (ipc):', f1)
    assert 'Nacional' in f1, f'{version}: f1 no trae Nacional -> {f1}'
    assert not any(x.isdigit() for x in f1), f'{version}: f1 trae años -> {f1}'

    # 3) segundo filtro = clasificaciones
    page.select_option('#pg-f1', 'Nacional')
    page.wait_for_timeout(400)
    f2 = opts(page, '#pg-f2')
    print('  f2:', f2)
    assert 'COICOP' in f2, f'{version}: f2 no trae COICOP -> {f2}'

    # 4) tercer filtro = codigos
    page.select_option('#pg-f2', 'COICOP')
    page.wait_for_timeout(400)
    f3 = opts(page, '#pg-f3')
    print('  f3:', f3[:6], '...' if len(f3) > 6 else '')
    assert '0' in f3, f'{version}: f3 no trae codigo 0 -> {f3}'

    # 5) url construida
    url = page.text_content('#pg-url')
    print('  url:', url)

    # 6) ejecutar -> respuesta real
    page.fill('#pg-year', '2023')
    page.wait_for_timeout(200)
    page.click('#pg-run')
    page.wait_for_timeout(1500)
    st = (page.text_content(STATUS[version]) or '').strip()
    body = (page.text_content(OUT[version]) or '')[:80].replace('\n', ' ')
    print('  status:', st)
    print('  body  :', body)
    assert '200 OK' in st, f'{version}: status no 200 -> {st}'

    # 7) cambiar a cba-cbt y emae
    page.select_option('#pg-ind', 'cba-cbt')
    page.wait_for_timeout(900)
    c1 = opts(page, '#pg-f1')
    print('  cba f1:', c1)
    assert 'adulto-equivalente' in c1, f'{version}: cba f1 -> {c1}'

    page.select_option('#pg-ind', 'emae')
    page.wait_for_timeout(900)
    e1 = opts(page, '#pg-f1')
    print('  emae f1:', e1)
    assert 'sectores' in e1, f'{version}: emae f1 -> {e1}'

    page.select_option('#pg-f1', 'sectores')
    page.wait_for_timeout(600)
    e2 = opts(page, '#pg-f2')
    print('  emae f2:', e2)
    assert 'A' in e2, f'{version}: emae f2 -> {e2}'

    # 8) ica sin subcategorias
    page.select_option('#pg-ind', 'ica')
    page.wait_for_timeout(900)
    i1 = opts(page, '#pg-f1')
    print('  ica f1 (debe estar vacio):', i1)

    if errors:
        print('  !! errores de consola:', errors)
        raise SystemExit(f'{version}: errores de consola')
    print('  OK')


def main():
    versions = sys.argv[1:] or ['version-a', 'version-b', 'version-c', 'version-d', 'version-e', 'version-f']
    os.makedirs(SHOTS, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for v in versions:
            ctx = browser.new_context(viewport={'width': 1440, 'height': 960})
            page = ctx.new_page()
            errors = []
            page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
            page.on('pageerror', lambda e: errors.append(str(e)))
            try:
                check(v, page, errors)
            finally:
                page.goto(f'{BASE}/{v}/index.html', wait_until='networkidle')
                page.wait_for_timeout(600)
                page.add_style_tag(content='.reveal{opacity:1!important;transform:none!important;transition:none!important}')
                page.wait_for_timeout(400)
                page.screenshot(path=f'{SHOTS}/{v}-desktop.png', full_page=True)
                page.set_viewport_size({'width': 390, 'height': 844})
                page.wait_for_timeout(800)
                page.screenshot(path=f'{SHOTS}/{v}-mobile.png', full_page=True)
                ctx.close()
        browser.close()
    print('\nscreenshots en', SHOTS)


if __name__ == '__main__':
    main()
