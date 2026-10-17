import sys, json
from playwright.sync_api import sync_playwright
U=sys.argv[1]; AX=open(sys.argv[2] if len(sys.argv)>2 else '/tmp/axe/package/axe.min.js').read()
bad=0
with sync_playwright() as p:
    b=p.chromium.launch()
    for name,vp,theme,dialog in [("desktop light",(1400,900),"light",False),("desktop dark",(1400,900),"dark",False),("mobile light",(390,844),"light",False),("search dialog",(1400,900),"light",True)]:
        pg=b.new_page(viewport={"width":vp[0],"height":vp[1]}); pg.goto(U); pg.wait_for_load_state("networkidle")
        pg.evaluate(f"document.documentElement.dataset.theme='{theme}'")
        if dialog: pg.keyboard.press("Control+k"); pg.fill("#pal-q","sync")
        pg.evaluate(AX)
        r=pg.evaluate("axe.run(document,{runOnly:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa','best-practice']})")
        print(f"{name}: {len(r['violations'])} violations, {len(r['incomplete'])} need review")
        for v in r['violations']:
            bad+=1; print("  -",v['id'],v['impact'],f"({len(v['nodes'])})",v['help']); [print("      ",n['target'][0] if n['target'] else '') for n in v['nodes'][:3]]
        pg.close()
    b.close()
sys.exit(1 if bad else 0)
