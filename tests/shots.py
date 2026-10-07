"""Screenshots -> tests/shots/*.png"""
import os
from playwright.sync_api import sync_playwright
CH='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
ROOT=__file__.rsplit('/tests/',1)[0]; URL='file://'+ROOT+'/index.html'; OUT=ROOT+'/tests/shots'; os.makedirs(OUT,exist_ok=True)
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=CH,args=['--no-sandbox']); pg=b.new_page(viewport={'width':900,'height':540})
    pg.add_init_script('window.__JJmanual=true;'); pg.goto(URL); pg.wait_for_timeout(500)
    def snap(n,fr=3):
        pg.evaluate(f'for(let i=0;i<{fr};i++)__JJ.step();__JJ.draw();0'); pg.wait_for_timeout(100); pg.screenshot(path=f'{OUT}/{n}.png')
    snap('1_title'); pg.evaluate('__JJ.state="select";0'); snap('2_select')
    for i in range(5):
        pg.evaluate(f'__JJ.startLevel({i});0'); pg.evaluate('__JJ.down.right=true;0'); snap(f'3_level{i+1}',150)
    pg.evaluate('__JJ.startLevel(4);0'); pg.evaluate('(()=>{const D=__JJ;D.P.x=(D.LV.W-30)*16;D.down.right=false;D.hit.add("shoot")})();0'); snap('4_boss',50)
    pg.evaluate('__JJ.finishLevel();0'); snap('5_levelend',60); pg.evaluate('__JJ.state="ending";0'); snap('6_ending',60)
    b.close()
