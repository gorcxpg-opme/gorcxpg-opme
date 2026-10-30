#!/usr/bin/env python3
"""Gera as imagens do perfil (tema claro e escuro) e a seção de certificados do README.

Lê:   dados/perfil.json, dados/certificados.csv e, se existir, dados/linkedin/Certifications.csv
Grava: assets/*.svg e o trecho do README.md entre os marcadores CERTIFICADOS e HORAS.

Só usa a biblioteca padrão do Python 3.9+. Roda todo dia pelo GitHub Actions
(.github/workflows/perfil.yml), e também na sua máquina:  python scripts/gerar_perfil.py
"""
from __future__ import annotations

import csv
import html
import json
import re
import sys
import unicodedata
from collections import OrderedDict, defaultdict
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "dados"
ASSETS = RAIZ / "assets"
README = RAIZ / "README.md"
FUSO = ZoneInfo("America/Sao_Paulo")

SANS = "'Segoe UI','Inter',system-ui,-apple-system,'Helvetica Neue',Arial,sans-serif"
MONO = "'Cascadia Code','JetBrains Mono',ui-monospace,'SF Mono',Consolas,'Liberation Mono',monospace"

TEMAS = {
    "escuro": dict(
        fundo="#0b1220", fundo2="#0e1830", painel="#111c33", borda="#22314f", grade="#15213a",
        texto="#e7edf8", suave="#93a3c0", fraco="#5d6d8c",
        azul="#6b8cff", verde="#2dd4bf", laranja="#f5a524", violeta="#b197fc", ok="#34d399",
        brilho="0.20",
    ),
    "claro": dict(
        fundo="#f7f9fd", fundo2="#eef2fa", painel="#ffffff", borda="#d8e0ee", grade="#e7ecf6",
        texto="#0f172a", suave="#475569", fraco="#94a3b8",
        azul="#2f4fd0", verde="#0f9488", laranja="#d97706", violeta="#7c4ddb", ok="#15935b",
        brilho="0.10",
    ),
}
COR_GRUPO = {"laranja": "laranja", "azul": "azul", "verde": "verde", "violeta": "violeta"}
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


# ───────────────────────── utilidades ─────────────────────────

def esc(s) -> str:
    return html.escape(str(s), quote=True)


def hoje() -> date:
    return datetime.now(FUSO).date()


def iso(s: str) -> date:
    return date.fromisoformat(s)


def br(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def chave(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def largura(texto: str, fs: float, mono: bool = False, negrito: bool = False) -> float:
    """Estimativa da largura do texto em unidades do SVG (sem fonte carregada não dá para medir)."""
    if mono:
        return len(texto) * 0.6 * fs
    w = 0.0
    for c in texto:
        if c in "il.,:;'|!·()[]":
            w += 0.28
        elif c == " ":
            w += 0.28
        elif c in "mwMW@":
            w += 0.84
        elif c.isupper():
            w += 0.66
        elif c.isdigit():
            w += 0.56
        else:
            w += 0.52
    return w * fs * (1.06 if negrito else 1.0)


def caber(texto: str, fs: float, maxw: float, **kw) -> float:
    """Diminui a fonte até o texto caber na largura."""
    while fs > 9 and largura(texto, fs, **kw) > maxw:
        fs -= 0.5
    return fs


def quebrar(texto: str, fs: float, maxw: float, **kw) -> list[str]:
    linhas, atual = [], ""
    for p in texto.split():
        teste = f"{atual} {p}".strip()
        if atual and largura(teste, fs, **kw) > maxw:
            linhas.append(atual)
            atual = p
        else:
            atual = teste
    if atual:
        linhas.append(atual)
    return linhas


def num(n: float) -> str:
    if abs(n - round(n)) < 1e-9:
        return f"{n:,.0f}".replace(",", ".")
    return f"{n:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")


def css_base(t: dict, extra: str = "") -> str:
    return f"""<style>
.s{{font-family:{SANS}}} .m{{font-family:{MONO}}}
@keyframes entra{{from{{opacity:0;transform:translateY(12px)}}to{{opacity:1;transform:none}}}}
.entra{{animation:entra .8s cubic-bezier(.2,.7,.2,1) both}}
@keyframes fluxo{{to{{stroke-dashoffset:-64}}}}
.fluxo{{stroke-dasharray:6 10;animation:fluxo 2.2s linear infinite}}
@keyframes pisca{{50%{{opacity:0}}}}
.pisca{{animation:pisca 1.05s steps(1) infinite}}
@keyframes flutua{{50%{{transform:translateY(-7px)}}}}
.flutua{{animation:flutua 4.5s ease-in-out infinite}}
@keyframes pulsa{{0%{{opacity:.6;transform:scale(1)}}100%{{opacity:0;transform:scale(2.6)}}}}
.pulsa{{transform-box:fill-box;transform-origin:center;animation:pulsa 2.2s ease-out infinite}}
@keyframes onda{{0%{{opacity:.7;transform:scale(1)}}100%{{opacity:0;transform:scale(1.55)}}}}
.onda{{transform-box:fill-box;transform-origin:center;animation:onda 2.8s ease-out infinite}}
@keyframes respira{{50%{{opacity:.45}}}}
.respira{{animation:respira 2.4s ease-in-out infinite}}
{extra}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
</style>"""


def documento(w: int, h: int, t: dict, titulo: str, corpo: str, extra_css: str = "", defs: str = "") -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{esc(titulo)}">
<title>{esc(titulo)}</title>
{css_base(t, extra_css)}
<defs>
<pattern id="grade" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="{t['grade']}" stroke-width="1"/></pattern>
<linearGradient id="gAzulVerde" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="{t['azul']}"/><stop offset="1" stop-color="{t['verde']}"/></linearGradient>
<radialGradient id="gBrilho" cx="0.82" cy="0.35" r="0.6"><stop offset="0" stop-color="{t['azul']}" stop-opacity="{t['brilho']}"/><stop offset="1" stop-color="{t['azul']}" stop-opacity="0"/></radialGradient>
<clipPath id="cartao"><rect width="{w}" height="{h}" rx="20"/></clipPath>
{defs}
</defs>
<g clip-path="url(#cartao)">
<rect width="{w}" height="{h}" fill="{t['fundo']}"/>
<rect width="{w}" height="{h}" fill="url(#grade)" opacity=".55"/>
<rect width="{w}" height="{h}" fill="url(#gBrilho)"/>
{corpo}
</g>
<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="20" fill="none" stroke="{t['borda']}"/>
</svg>
"""


def smil_discreto(atributo: str, pontos: list[tuple[float, float]], total: float) -> str:
    """Animação discreta (valores mudam em degraus) repetida para sempre."""
    limpos: "OrderedDict[float, float]" = OrderedDict()
    for tempo, valor in sorted(pontos, key=lambda p: p[0]):
        limpos[round(min(max(tempo / total, 0), 1), 4)] = valor
    if 0.0 not in limpos:
        limpos = OrderedDict([(0.0, 0.0), *limpos.items()])
    tempos = list(limpos.keys())
    valores = [f"{v:.1f}" for v in limpos.values()]
    return (f'<animate attributeName="{atributo}" dur="{total:.2f}s" repeatCount="indefinite" calcMode="discrete" '
            f'keyTimes="{";".join(f"{x:g}" for x in tempos)}" values="{";".join(valores)}"/>')


# ───────────────────────── banner ─────────────────────────

def banner(cfg: dict, t: dict) -> str:
    W, H = 1200, 360
    p = []

    # texto da esquerda
    p.append(f'<g class="entra"><text x="56" y="76" class="m" font-size="16" fill="{t["verde"]}" letter-spacing="1">// {esc(cfg["local"])}</text></g>')
    nome_fs = caber(cfg["nome"], 64, 600, negrito=True)
    p.append(f'<g class="entra" style="animation-delay:.1s"><text x="54" y="146" class="s" font-size="{nome_fs}" font-weight="800" fill="{t["texto"]}" letter-spacing="-1">{esc(cfg["nome"])}</text></g>')
    papel_fs = caber(cfg["papel"], 24, 620)
    p.append(f'<g class="entra" style="animation-delay:.2s"><text x="56" y="188" class="s" font-size="{papel_fs}" fill="{t["suave"]}">{esc(cfg["papel"])}</text></g>')

    # terminal com digitação
    fs, slot = 20, 6.0
    cw = 0.6 * fs
    frases = [f[:44] for f in cfg["frases"]]
    total = slot * len(frases)
    tx, ty = 104, 256
    defs, textos, cursor = [], [], []
    for i, f in enumerate(frases):
        n = len(f)
        t0 = i * slot
        passo = min(0.075, 2.6 / max(n, 1))
        pts = [(t0, 0)]
        for k in range(1, n + 1):
            pts.append((t0 + k * passo, k * cw))
        fim_digitacao = t0 + n * passo
        apaga = t0 + slot - 0.35 - n * 0.018
        apaga = max(apaga, fim_digitacao + 1.2)
        for k in range(n - 1, -1, -1):
            pts.append((apaga + (n - k) * 0.018, k * cw))
        cursor.extend(pts)
        defs.append(f'<clipPath id="dig{i}"><rect x="{tx}" y="{ty-22}" height="32" width="0">{smil_discreto("width", pts, total)}</rect></clipPath>')
        textos.append(f'<text x="{tx}" y="{ty}" class="m" font-size="{fs}" fill="{t["texto"]}" textLength="{n*cw:.1f}" lengthAdjust="spacingAndGlyphs" clip-path="url(#dig{i})">{esc(f)}</text>')
    cursor_x = [(tm, tx + v + 2) for tm, v in cursor]
    p.append(f'<g class="entra" style="animation-delay:.3s">'
             f'<rect x="56" y="222" width="620" height="52" rx="12" fill="{t["painel"]}" stroke="{t["borda"]}"/>'
             f'<text x="76" y="256" class="m" font-size="20" fill="{t["verde"]}">❯</text>'
             + "".join(textos) +
             f'<rect class="pisca" x="{tx}" y="{ty-18}" width="{cw*0.55:.1f}" height="22" fill="{t["verde"]}">{smil_discreto("x", cursor_x, total)}</rect>'
             '</g>')

    # selos
    s1 = cfg["status"]
    w1 = largura(s1, 15) + 52
    s2 = "LinkedIn · gabriel-cunha-xp"
    p.append(f'<g class="entra" style="animation-delay:.45s">'
             f'<rect x="56" y="296" width="{w1:.0f}" height="34" rx="17" fill="{t["painel"]}" stroke="{t["borda"]}"/>'
             f'<circle cx="77" cy="313" r="5" fill="{t["ok"]}"/><circle class="pulsa" cx="77" cy="313" r="5" fill="{t["ok"]}"/>'
             f'<text x="92" y="318" class="s" font-size="15" fill="{t["texto"]}">{esc(s1)}</text>'
             f'<rect x="{56+w1+12:.0f}" y="296" width="{largura(s2,15)+36:.0f}" height="34" rx="17" fill="none" stroke="{t["borda"]}"/>'
             f'<text x="{56+w1+30:.0f}" y="318" class="s" font-size="15" fill="{t["suave"]}">{esc(s2)}</text>'
             '</g>')

    # rede da direita: fornecedores → almoxarifado → hospitais
    forn = [(770, 112), (746, 192), (770, 272)]
    cd = (948, 192)
    hosp = [(1118, 112), (1142, 192), (1118, 272)]
    caminhos = []
    for i, (x, y) in enumerate(forn):
        caminhos.append((f"c{i}", f"M{x+16},{y} C{x+90},{y} {cd[0]-110},{cd[1]} {cd[0]-36},{cd[1]}", t["laranja"]))
    for i, (x, y) in enumerate(hosp):
        caminhos.append((f"c{i+3}", f"M{cd[0]+36},{cd[1]} C{cd[0]+110},{cd[1]} {x-90},{y} {x-18},{y}", t["verde"]))
    rede = [f'<g opacity=".95">']
    for cid, d, cor in caminhos:
        rede.append(f'<path id="{cid}" d="{d}" fill="none" stroke="{t["borda"]}" stroke-width="2"/>')
        rede.append(f'<path class="fluxo" d="{d}" fill="none" stroke="{cor}" stroke-width="2" opacity=".75"/>')
    for k, (cid, _d, cor) in enumerate(caminhos):
        dur = 3.0 + (k % 3) * 0.45
        for j in range(2):
            rede.append(f'<circle r="4.5" fill="{cor}"><animateMotion dur="{dur:.2f}s" repeatCount="indefinite" begin="-{(j*dur/2 + k*0.37):.2f}s"><mpath href="#{cid}" xlink:href="#{cid}"/></animateMotion></circle>')
    # nós
    for x, y in forn:
        rede.append(f'<rect x="{x-16}" y="{y-16}" width="32" height="32" rx="8" fill="{t["painel"]}" stroke="{t["laranja"]}" stroke-width="2"/>'
                    f'<path d="M{x-7},{y-3} l7,-4 7,4 v8 l-7,4 -7,-4z M{x-7},{y-3} l7,4 7,-4 M{x},{y+1} v8" fill="none" stroke="{t["laranja"]}" stroke-width="1.6" stroke-linejoin="round"/>')
    for x, y in hosp:
        rede.append(f'<circle cx="{x}" cy="{y}" r="17" fill="{t["painel"]}" stroke="{t["verde"]}" stroke-width="2"/>'
                    f'<path d="M{x},{y-8} v16 M{x-8},{y} h16" stroke="{t["verde"]}" stroke-width="3" stroke-linecap="round"/>')
    x, y = cd
    rede.append(f'<rect class="onda" x="{x-34}" y="{y-34}" width="68" height="68" rx="16" fill="none" stroke="{t["azul"]}" stroke-width="2"/>'
                f'<rect x="{x-34}" y="{y-34}" width="68" height="68" rx="16" fill="{t["azul"]}"/>'
                f'<path d="M{x-17},{y+15} v-17 l17,-11 17,11 v17 M{x-9},{y+15} v-10 h18 v10 M{x-9},{y+5} h18" fill="none" stroke="{t["fundo"]}" stroke-width="2.6" stroke-linejoin="round"/>')
    # rótulos
    for rx_, rot, cor in ((758, "FORNECEDORES", t["laranja"]), (948, "ALMOXARIFADO", t["azul"]), (1130, "HOSPITAIS", t["verde"])):
        rede.append(f'<text x="{rx_}" y="56" text-anchor="middle" class="m" font-size="13" fill="{cor}" letter-spacing="1.5">{rot}</text>')
    # etiquetas que flutuam
    for (ex, ey, txt, atraso) in ((948, 104, "ABC/XYZ · ROP", 0), (948, 292, "FEFO · lote · validade", 1.6)):
        ew = largura(txt, 13, mono=True) + 22
        rede.append(f'<g class="flutua" style="animation-delay:-{atraso}s"><rect x="{ex-ew/2:.1f}" y="{ey-15}" width="{ew:.1f}" height="26" rx="13" fill="{t["fundo2"]}" stroke="{t["borda"]}"/>'
                    f'<text x="{ex}" y="{ey+3}" text-anchor="middle" class="m" font-size="13" fill="{t["suave"]}">{esc(txt)}</text></g>')
    rede.append("</g>")
    p.append("".join(rede))

    return documento(W, H, t, f'{cfg["nome"]} — {cfg["papel"]}', "\n".join(p), defs="".join(defs))


# ───────────────────────── projeto ─────────────────────────

def projeto(cfg: dict, t: dict) -> str:
    W, H = 1200, 452
    pj = cfg["projeto"]
    p = []
    p.append(f'<text x="40" y="54" class="m" font-size="14" fill="{t["verde"]}" letter-spacing="1.5">SUPPLY OPME · NÚMEROS DO SISTEMA</text>')
    p.append(f'<text x="600" y="54" class="m" font-size="14" fill="{t["verde"]}" letter-spacing="1.5">MÓDULOS · O QUE O GESTOR PERGUNTA</text>')
    # métricas 2x2
    for i, m in enumerate(pj["metricas"][:4]):
        cx, cy = 40 + (i % 2) * 268, 76 + (i // 2) * 146
        val_fs = caber(m["valor"], 46, 220, negrito=True)
        linhas = quebrar(m["rotulo"], 15, 216)[:2]
        p.append(f'<g class="entra" style="animation-delay:{0.1 + i*0.12:.2f}s">'
                 f'<rect x="{cx}" y="{cy}" width="252" height="130" rx="14" fill="{t["painel"]}" stroke="{t["borda"]}"/>'
                 f'<rect x="{cx}" y="{cy+22}" width="3" height="40" rx="1.5" fill="{t["azul"]}"/>'
                 f'<text x="{cx+20}" y="{cy+62}" class="s" font-size="{val_fs}" font-weight="800" fill="{t["texto"]}">{esc(m["valor"])}</text>'
                 + "".join(f'<text x="{cx+20}" y="{cy+90+k*19}" class="s" font-size="15" fill="{t["suave"]}">{esc(l)}</text>' for k, l in enumerate(linhas))
                 + "</g>")
    # módulos
    cores = {"no ar": t["ok"], "em construção": t["laranja"], "planejado": t["fraco"]}
    y0, alt, gap = 76, 46, 10
    mods = pj["modulos"][:5]
    for i, m in enumerate(mods):
        y = y0 + i * (alt + gap)
        cor = cores.get(m["status"], t["fraco"])
        nome_fs = caber(m["nome"], 17, 192, negrito=True)
        sw = largura(m["status"], 13) + 24
        perg_fs = caber(m["pergunta"], 15, 1148 - sw - 34 - 846)
        anel = f'<circle class="pulsa" cx="622" cy="{y+alt/2}" r="5" fill="{cor}"/>' if m["status"] == "no ar" else ""
        p.append(f'<g class="entra" style="animation-delay:{0.2 + i*0.12:.2f}s">'
                 f'<rect x="600" y="{y}" width="560" height="{alt}" rx="11" fill="{t["painel"]}" stroke="{t["borda"]}"/>'
                 f'<circle cx="622" cy="{y+alt/2}" r="5" fill="{cor}"/>{anel}'
                 f'<text x="640" y="{y+29}" class="s" font-size="{nome_fs}" font-weight="700" fill="{t["texto"]}">{esc(m["nome"])}</text>'
                 f'<text x="846" y="{y+29}" class="s" font-size="{perg_fs}" fill="{t["suave"]}">{esc(m["pergunta"])}</text>'
                 f'<rect x="{1148-sw:.1f}" y="{y+11}" width="{sw:.1f}" height="24" rx="12" fill="none" stroke="{cor}"/>'
                 f'<text x="{1148-sw/2:.1f}" y="{y+27.5}" text-anchor="middle" class="s" font-size="13" fill="{cor}">{esc(m["status"])}</text>'
                 '</g>')
    # faixa que "varre" os módulos
    curso = (len(mods) - 1) * (alt + gap)
    p.append(f'<rect class="varre" x="600" y="{y0}" width="560" height="{alt}" rx="11" fill="url(#gAzulVerde)" opacity=".10"/>')
    extra_css = (f"@keyframes varre{{0%,8%{{transform:translateY(0)}}92%,100%{{transform:translateY({curso}px)}}}}"
                 ".varre{animation:varre 6s cubic-bezier(.6,0,.4,1) infinite alternate}")
    # extras
    y = 392
    p.append(f'<text x="40" y="{y+24}" class="m" font-size="13" fill="{t["fraco"]}" letter-spacing="1.2">TAMBÉM NO SISTEMA</text>')
    x = 236
    for i, e in enumerate(pj.get("extras", [])):
        ew = largura(e, 15) + 30
        if x + ew > 1160:
            break
        p.append(f'<g class="entra" style="animation-delay:{0.8 + i*0.1:.2f}s"><rect x="{x:.1f}" y="{y}" width="{ew:.1f}" height="36" rx="18" fill="{t["fundo2"]}" stroke="{t["borda"]}"/>'
                 f'<text x="{x+15:.1f}" y="{y+23}" class="s" font-size="15" fill="{t["texto"]}">{esc(e)}</text></g>')
        x += ew + 10
    return documento(W, H, t, "Supply OPME — números do sistema e módulos", "\n".join(p), extra_css)


# ───────────────────────── roadmap ─────────────────────────

def roadmap(cfg: dict, t: dict, dia: date) -> str:
    W, H = 1200, 356
    rm = cfg["roadmap"]
    ini, fim, lanc = iso(rm["inicio_grafico"]), iso(rm["fim_grafico"]), iso(rm["lancamento"])
    x0, x1, yb = 60, 1140, 214

    def X(d: date) -> float:
        d = min(max(d, ini), fim)
        return x0 + (d - ini).days / (fim - ini).days * (x1 - x0)

    fases = rm["fases"]
    atual = next((f for f in fases if iso(f["inicio"]) <= dia <= iso(f["fim"])), None)
    p = []
    p.append(f'<text x="48" y="58" class="m" font-size="14" fill="{t["verde"]}" letter-spacing="1.5">ROADMAP · SUPPLY OPME</text>')
    p.append(f'<text x="46" y="98" class="s" font-size="32" font-weight="800" fill="{t["texto"]}">Do protótipo ao lançamento</text>')
    if atual:
        sub = f'Agora: {atual["nome"]} — {atual["descricao"]}'
    elif dia < ini:
        sub = "Em preparação"
    else:
        sub = "Supply OPME no mercado"
    p.append(f'<text x="48" y="128" class="s" font-size="{caber(sub, 17, 760)}" fill="{t["suave"]}">{esc(sub)}</text>')

    faltam = (lanc - dia).days
    if faltam > 0:
        p.append(f'<text x="1152" y="92" text-anchor="end" class="s" font-size="56" font-weight="800" fill="{t["azul"]}">{num(faltam)}</text>'
                 f'<text x="1152" y="122" text-anchor="end" class="s" font-size="16" fill="{t["suave"]}">dias para o lançamento · {br(lanc)}</text>')
    else:
        p.append(f'<text x="1152" y="92" text-anchor="end" class="s" font-size="44" font-weight="800" fill="{t["ok"]}">no mercado</text>'
                 f'<text x="1152" y="122" text-anchor="end" class="s" font-size="16" fill="{t["suave"]}">desde {br(lanc)}</text>')

    # barra
    p.append(f'<rect x="{x0}" y="{yb}" width="{x1-x0}" height="10" rx="5" fill="{t["grade"]}"/>')
    xh = X(dia)
    if xh > x0:
        p.append(f'<rect x="{x0}" y="{yb}" width="{xh-x0:.1f}" height="10" rx="5" fill="url(#gAzulVerde)">'
                 f'<animate attributeName="width" from="0" to="{xh-x0:.1f}" dur="1.6s" fill="freeze" calcMode="spline" keySplines=".2 .7 .2 1" keyTimes="0;1"/></rect>')
    # fases
    for i, f in enumerate(fases):
        fi, ff = iso(f["inicio"]), iso(f["fim"])
        xa, xb = X(fi), X(ff)
        if i > 0:
            p.append(f'<rect x="{xa-1:.1f}" y="{yb-4}" width="2" height="18" rx="1" fill="{t["borda"]}"/>')
        meio = (xa + xb) / 2
        if ff < dia:
            cor, peso, prefixo = t["suave"], "500", "✓ "
        elif fi <= dia <= ff:
            cor, peso, prefixo = t["azul"], "800", ""
        else:
            cor, peso, prefixo = t["fraco"], "500", ""
        rotulo = prefixo + f["nome"]
        fs = caber(rotulo, 15, 128, negrito=peso == "800")
        y = yb - 46 if i % 2 == 0 else yb + 50
        guia_y1, guia_y2 = (y + 8, yb - 4) if i % 2 == 0 else (yb + 14, y - 16)
        p.append(f'<g class="entra" style="animation-delay:{0.1 + i*0.05:.2f}s">'
                 f'<line x1="{meio:.1f}" x2="{meio:.1f}" y1="{guia_y1}" y2="{guia_y2}" stroke="{t["borda"]}" stroke-dasharray="2 3"/>'
                 f'<text x="{meio:.1f}" y="{y}" text-anchor="middle" class="s" font-size="{fs}" font-weight="{peso}" fill="{cor}">{esc(rotulo)}</text></g>')
    # bandeira do lançamento
    xl = X(lanc)
    p.append(f'<g><line x1="{xl:.1f}" x2="{xl:.1f}" y1="{yb-22}" y2="{yb+10}" stroke="{t["laranja"]}" stroke-width="2"/>'
             f'<path d="M{xl:.1f},{yb-22} l16,5 -16,5z" fill="{t["laranja"]}"/></g>')
    # meses
    d = date(ini.year, ini.month, 1)
    while d <= fim:
        xm = X(d)
        rot = MESES[d.month - 1] + (f" {str(d.year)[2:]}" if d.month == 1 or d == date(ini.year, ini.month, 1) else "")
        p.append(f'<text x="{xm+4:.1f}" y="{yb+92}" class="m" font-size="12" fill="{t["fraco"]}">{rot}</text>')
        d = date(d.year + (d.month == 12), d.month % 12 + 1, 1)
    # hoje
    if ini <= dia <= fim:
        p.append(f'<circle class="pulsa" cx="{xh:.1f}" cy="{yb+5}" r="9" fill="{t["verde"]}"/>'
                 f'<circle cx="{xh:.1f}" cy="{yb+5}" r="9" fill="{t["verde"]}" stroke="{t["fundo"]}" stroke-width="3"/>'
                 f'<text x="{xh:.1f}" y="{yb-20}" text-anchor="middle" class="m" font-size="12" font-weight="700" fill="{t["verde"]}">hoje · {dia.strftime("%d/%m")}</text>')
    return documento(W, H, t, "Roadmap do Supply OPME até o lançamento", "\n".join(p))


# ───────────────────────── stack ─────────────────────────

def stack(cfg: dict, t: dict) -> str:
    grupos = cfg["stack"][:4]
    maxi = max(len(g["itens"]) for g in grupos)
    W, H = 1200, 98 + maxi * 46 + 28
    cw, gap = 266, 18
    p = []
    for gi, g in enumerate(grupos):
        x = 40 + gi * (cw + gap)
        cor = t[COR_GRUPO.get(g.get("cor"), "azul")]
        p.append(f'<g class="entra" style="animation-delay:{gi*0.1:.2f}s"><rect x="{x}" y="38" width="12" height="12" rx="3" fill="{cor}"/>'
                 f'<text x="{x+22}" y="50" class="s" font-size="{caber(g["grupo"], 18, cw-24, negrito=True)}" font-weight="700" fill="{t["texto"]}">{esc(g["grupo"])}</text></g>')
        for ii, item in enumerate(g["itens"]):
            y = 70 + ii * 46
            fs = caber(item, 15, cw - 34)
            p.append(f'<g class="entra" style="animation-delay:{0.15 + gi*0.1 + ii*0.07:.2f}s">'
                     f'<rect x="{x}" y="{y}" width="{cw}" height="36" rx="9" fill="{t["painel"]}" stroke="{t["borda"]}"/>'
                     f'<rect x="{x}" y="{y+9}" width="3" height="18" rx="1.5" fill="{cor}"/>'
                     f'<text x="{x+16}" y="{y+23}" class="s" font-size="{fs}" fill="{t["texto"]}">{esc(item)}</text></g>')
    return documento(W, H, t, "Ferramentas e conhecimentos", "\n".join(p))


# ───────────────────────── certificados ─────────────────────────

REGRAS_AREA = [
    ("Qualidade & Lean", ["iso", "auditor", "qualidade", "seis sigma", "six sigma", "lean", "5s", "kaizen"]),
    ("Gestão & agilidade", ["scrum", "agil", "agilidade", "gestao", "lean", "six sigma", "lideranca", "kanban", "projeto"]),
    ("Supply chain & operações", ["supply", "logistica", "estoque", "compras", "sap", "mrp", "cadeia", "suprimentos", "armazen"]),
    ("Excel & VBA", ["excel", "vba", "planilha", "procv"]),
    ("BI & visualização", ["power bi", "dashboard", "visualiza", "business intelligence", "olap", "mdx", "report", "pentaho", "tableau", "looker", "data warehouse"]),
    ("Bancos de dados & SQL", ["sql", "mysql", "postgres", "oracle", "banco de dados"]),
    ("Engenharia de dados", ["airflow", "databricks", "spark", "etl", "pipeline", "data mesh", "aws", "azure", "linux", "docker", "beam", "cloud", "nuvem"]),
    ("Estatística & forecast", ["estatistica", "regressao", "series temporais", "previs", "probabilidade", "hipotese"]),
    ("Programação & Git", ["git", "github", "logica de programacao", "open source", "versionamento"]),
    ("IA aplicada", ["copilot", "genai", "chatgpt", "llm", "inteligencia artificial", "ai now", "agents", "prompt"]),
    ("Python & data science", ["python", "pandas", "numpy", "data science", "machine learning", "nlp", "ciencia de dados", "inteligencia artificial"]),
]


def adivinhar_area(curso: str) -> str:
    k = f" {chave(curso)} "
    for area, palavras in REGRAS_AREA:
        if any(f" {p}" in k for p in palavras):
            return area
    return "Outros"


def data_flex(s: str):
    """Aceita dd/mm/aaaa, mm/aaaa, aaaa-mm-dd, aaaa, 'Aug 2023' e 'ago de 2023'."""
    s = (s or "").strip()
    if not s:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%m/%Y", "%Y-%m", "%Y", "%b %Y", "%B %Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    m = re.match(r"([a-zç]{3})\w*\.?\s+(?:de\s+)?(\d{4})", s.lower())
    if m and m.group(1) in MESES:
        return date(int(m.group(2)), MESES.index(m.group(1)) + 1, 1)
    return None


def carregar_certificados() -> list[dict]:
    regs = []
    arq = DADOS / "certificados.csv"
    with arq.open(encoding="utf-8-sig", newline="") as f:
        for n, r in enumerate(csv.DictReader(f), start=2):
            curso = (r.get("curso") or "").strip()
            if not curso or chave(r.get("exibir") or "") in {"nao", "n", "0", "false", "oculto"}:
                continue
            try:
                horas = float((r.get("horas") or "0").replace(",", "."))
            except ValueError:
                print(f"aviso: horas inválidas na linha {n} de certificados.csv: {r.get('horas')!r}", file=sys.stderr)
                horas = 0.0
            regs.append(dict(
                instituicao=(r.get("instituicao") or "Outras").strip(),
                formacoes=[x.strip() for x in (r.get("formacao") or "").split(";") if x.strip()],
                curso=curso,
                area=(r.get("area") or "").strip() or adivinhar_area(curso),
                horas=horas,
                conclusao=data_flex(r.get("conclusao")),
                link=(r.get("link") or "").strip(),
            ))
    # exportação do LinkedIn (opcional): dados/linkedin/Certifications.csv
    li = DADOS / "linkedin" / "Certifications.csv"
    if li.exists():
        conhecidos = {chave(r["curso"]) for r in regs}
        with li.open(encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                col = {chave(k): v for k, v in r.items() if k}
                curso = (col.get("name") or col.get("nome") or "").strip()
                if not curso or chave(curso) in conhecidos:
                    continue
                conhecidos.add(chave(curso))
                regs.append(dict(
                    instituicao=(col.get("authority") or col.get("organizacao emissora") or "LinkedIn").strip(),
                    formacoes=[], curso=curso, area=adivinhar_area(curso), horas=0.0,
                    conclusao=data_flex(col.get("finished on") or col.get("started on") or ""),
                    link=(col.get("url") or "").strip(),
                ))
    return regs


def resumo_certificados(regs: list[dict]) -> dict:
    unicos = OrderedDict()
    for r in regs:
        unicos.setdefault((chave(r["instituicao"]), chave(r["curso"])), r)
    u = list(unicos.values())
    por_area = defaultdict(float)
    cont_area = defaultdict(int)
    for r in u:
        por_area[r["area"]] += r["horas"]
        cont_area[r["area"]] += 1
    formacoes = {(r["instituicao"], f) for r in regs for f in r["formacoes"]}
    return dict(
        cursos=len(u),
        horas=sum(r["horas"] for r in u),
        formacoes=len(formacoes),
        instituicoes=sorted({r["instituicao"] for r in u}),
        areas=sorted(por_area.items(), key=lambda kv: (-cont_area[kv[0]], -kv[1], kv[0])),
        cont_area=cont_area,
    )


def rotulo_area(area: str, h: float, res: dict) -> str:
    n = res["cont_area"][area]
    txt = f"{n} {'curso' if n == 1 else 'cursos'}"
    return f"{txt} · {num(round(h))} h" if h else txt


def cartao_certificados(res: dict, t: dict, dia: date) -> str:
    areas = res["areas"]
    W = 1200
    H = max(84 + len(areas) * 40 + 36, 356)
    p = []
    p.append(f'<text x="40" y="54" class="m" font-size="14" fill="{t["verde"]}" letter-spacing="1.5">CERTIFICADOS · ATUALIZADO EM {br(dia)}</text>')
    stats = [(num(res["cursos"]), "cursos concluídos"), (num(int(res["horas"])), "horas registradas"),
             (num(res["formacoes"]), "formações e trilhas"),
             (num(len(res["instituicoes"])), "instituição" if len(res["instituicoes"]) == 1 else "instituições")]
    for i, (v, rot) in enumerate(stats):
        cx, cy = 40 + (i % 2) * 196, 78 + (i // 2) * 128
        p.append(f'<g class="entra" style="animation-delay:{0.08*i:.2f}s"><rect x="{cx}" y="{cy}" width="182" height="114" rx="14" fill="{t["painel"]}" stroke="{t["borda"]}"/>'
                 f'<text x="{cx+18}" y="{cy+56}" class="s" font-size="{caber(v, 42, 150, negrito=True)}" font-weight="800" fill="{t["texto"]}">{v}</text>'
                 f'<text x="{cx+18}" y="{cy+86}" class="s" font-size="15" fill="{t["suave"]}">{esc(rot)}</text></g>')
    inst = " · ".join(res["instituicoes"])
    p.append(f'<text x="40" y="{78+2*128+16}" class="s" font-size="{caber(inst, 14, 380)}" fill="{t["fraco"]}">{esc(inst)}</text>')

    # barras por área
    xl, xb, wb = 470, 712, 286
    maxn = max(res["cont_area"].values(), default=1) or 1
    p.append(f'<text x="{xl}" y="54" class="m" font-size="14" fill="{t["fraco"]}" letter-spacing="1.5">CURSOS POR ÁREA</text>')
    for i, (area, h) in enumerate(areas):
        y = 84 + i * 40
        w = max(4.0, res["cont_area"][area] / maxn * wb)
        atraso = 0.25 + i * 0.09
        p.append(f'<text x="{xl}" y="{y+19}" class="s" font-size="{caber(area, 16, 230)}" fill="{t["texto"]}">{esc(area)}</text>'
                 f'<rect x="{xb}" y="{y+6}" width="{wb}" height="16" rx="8" fill="{t["grade"]}"/>'
                 f'<rect x="{xb}" y="{y+6}" width="{w:.1f}" height="16" rx="8" fill="url(#gAzulVerde)">'
                 f'<animate attributeName="width" from="0" to="{w:.1f}" begin="{atraso:.2f}s" dur="1.2s" fill="freeze" calcMode="spline" keySplines=".2 .7 .2 1" keyTimes="0;1"/></rect>'
                 f'<text x="1160" y="{y+19}" text-anchor="end" class="m" font-size="14" fill="{t["suave"]}">{rotulo_area(area, h, res)}</text>')
    return documento(W, H, t, f'{res["cursos"]} cursos e {num(res["horas"])} horas de certificados', "\n".join(p))


def secao_certificados_md(regs: list[dict]) -> str:
    por_inst = OrderedDict()
    for r in regs:
        por_inst.setdefault(r["instituicao"], []).append(r)
    partes = []
    def peso(item):
        lista = item[1]
        return (-len({chave(r["curso"]) for r in lista}), -sum({chave(r["curso"]): r["horas"] for r in lista}.values()))

    for inst, lista in sorted(por_inst.items(), key=peso):
        links = {r["link"] for r in lista}
        link_unico = next(iter(links)) if len(links) == 1 else ""
        sem_links = links == {""}
        horas = sum({chave(r["curso"]): r["horas"] for r in lista}.values())
        qtd = len({chave(r['curso']) for r in lista})
        cab = f"**{inst}** · {qtd} {'curso' if qtd == 1 else 'cursos'}"
        if horas:
            cab += f" · {num(horas)} h"
        if link_unico:
            cab += f" · [{'certificado' if qtd == 1 else 'certificado completo'} ↗]({link_unico})"
        partes.append(cab + "\n")
        grupos = OrderedDict()
        for r in lista:
            tem_formacao = any(x["formacoes"] for x in lista)
            for f in (r["formacoes"] or [("Cursos avulsos · " if tem_formacao else "") + r["area"]]):
                grupos.setdefault(f, []).append(r)
        nomes_formacao = {f for r in lista for f in r["formacoes"]}

        def recente(item):
            datas = [r["conclusao"] for r in item[1] if r["conclusao"]]
            if item[0] in nomes_formacao:
                return (0, -(max(datas).toordinal() if datas else 0), 0)
            return (1, -len(item[1]), -(max(datas).toordinal() if datas else 0))

        for nome, itens in sorted(grupos.items(), key=recente):
            datas = [r["conclusao"] for r in itens if r["conclusao"]]
            h = sum(r["horas"] for r in itens)
            resumo = f"<b>{esc(nome)}</b> · {len(itens)} {'curso' if len(itens) == 1 else 'cursos'}"
            if h:
                resumo += f" · {num(h)} h"
            if datas:
                d = max(datas)
                resumo += f" · {MESES[d.month-1]}/{d.year}"
            col_link = not (link_unico or sem_links)
            linhas = ["| Curso | Área | Horas | Concluído |" + (" Link |" if col_link else ""),
                      "|---|---|--:|--:|" + (":-:|" if col_link else "")]
            for r in sorted(itens, key=lambda r: r["conclusao"] or date.min):
                c = r["conclusao"].strftime("%d/%m/%Y") if r["conclusao"] else "—"
                curso = r["curso"].replace("|", "/")
                linha = f"| {curso} | {r['area']} | {num(r['horas']) if r['horas'] else '—'} | {c} |"
                if col_link:
                    linha += f" [↗]({r['link']}) |" if r["link"] else " — |"
                linhas.append(linha)
            partes.append(f"<details>\n<summary>{resumo}</summary>\n\n" + "\n".join(linhas) + "\n\n</details>")
    return "\n\n".join(p.strip() for p in partes)


def trocar_marcador(texto: str, nome: str, conteudo: str, bloco: bool = True) -> str:
    if bloco:
        padrao = re.compile(rf"(<!-- {nome}:INICIO -->)(.*?)(<!-- {nome}:FIM -->)", re.S)
    else:
        padrao = re.compile(rf"(<!--{nome}-->)(.*?)(<!--/{nome}-->)", re.S)
    if not padrao.search(texto):
        print(f"aviso: marcador {nome} não encontrado no README", file=sys.stderr)
        return texto
    return padrao.sub(lambda m: m.group(1) + (f"\n{conteudo}\n" if bloco else conteudo) + m.group(3), texto)


# ───────────────────────── principal ─────────────────────────

def gravar(nome: str, conteudo: str) -> None:
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / nome).write_text(conteudo, encoding="utf-8")


def main() -> None:
    cfg = json.loads((DADOS / "perfil.json").read_text(encoding="utf-8"))
    dia = hoje()
    regs = carregar_certificados()
    res = resumo_certificados(regs)
    for nome_tema, t in TEMAS.items():
        gravar(f"banner-{nome_tema}.svg", banner(cfg, t))
        gravar(f"projeto-{nome_tema}.svg", projeto(cfg, t))
        gravar(f"roadmap-{nome_tema}.svg", roadmap(cfg, t, dia))
        gravar(f"stack-{nome_tema}.svg", stack(cfg, t))
        gravar(f"certificados-{nome_tema}.svg", cartao_certificados(res, t, dia))
    if README.exists():
        txt = README.read_text(encoding="utf-8")
        txt = trocar_marcador(txt, "CERTIFICADOS", secao_certificados_md(regs))
        txt = trocar_marcador(txt, "HORAS", num(int(res["horas"])), bloco=False)
        txt = re.sub(r"badge/certificados-[\d.]+%20cursos", f"badge/certificados-{res['cursos']}%20cursos", txt)
        README.write_text(txt, encoding="utf-8")
    print(f"ok · {res['cursos']} cursos · {num(res['horas'])} h · {res['formacoes']} formações · {br(dia)}")


if __name__ == "__main__":
    main()
