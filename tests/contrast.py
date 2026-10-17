import sys
from playwright.sync_api import sync_playwright
JS = r"""
() => {
  const parse = c => { const m = c.match(/[\d.]+/g).map(Number); return {r:m[0],g:m[1],b:m[2],a:m[3]===undefined?1:m[3]}; };
  const over = (f,b) => ({r:f.r*f.a+b.r*(1-f.a), g:f.g*f.a+b.g*(1-f.a), b:f.b*f.a+b.b*(1-f.a), a:1});
  const bgOf = el => { const chain=[]; for(let e=el;e;e=e.parentElement){ const c=parse(getComputedStyle(e).backgroundColor); chain.push(c); if(c.a===1) break; }
    let bg = chain[chain.length-1].a===1?chain[chain.length-1]:{r:255,g:255,b:255,a:1};
    for(let i=chain.length-2;i>=0;i--) bg=over(chain[i],bg); return bg; };
  const lum = c => { const f=v=>{v/=255;return v<=.03928?v/12.92:Math.pow((v+.055)/1.055,2.4)}; return .2126*f(c.r)+.7152*f(c.g)+.0722*f(c.b); };
  const out=[];
  for (const el of document.querySelectorAll('body *')) {
    if (!el.offsetParent && getComputedStyle(el).position!=='fixed') continue;
    const own=[...el.childNodes].some(n=>n.nodeType===3 && n.textContent.trim());
    if(!own) continue;
    const cs=getComputedStyle(el); const bg=bgOf(el); const fg=over(parse(cs.color),bg);
    const L1=lum(fg),L2=lum(bg); const ratio=(Math.max(L1,L2)+.05)/(Math.min(L1,L2)+.05);
    const size=parseFloat(cs.fontSize), bold=parseInt(cs.fontWeight)>=700;
    const need=(size>=24||(size>=18.66&&bold))?3:4.5;
    if(ratio<need) out.push({tag:el.tagName+'.'+el.className, text:el.textContent.trim().slice(0,30), ratio:+ratio.toFixed(2), need});
  }
  return out;
}
"""
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={"width":1400,"height":900})
    for theme in ("light","dark"):
        pg.goto(sys.argv[1]); pg.evaluate(f"document.documentElement.dataset.theme='{theme}'")
        # check gates both states
        pg.evaluate("document.querySelectorAll('input[data-gate]')[0].checked=true")
        r=pg.evaluate(JS); print(theme, len(r), "failures")
        for x in r[:25]: print("  ",x)
    b.close()
