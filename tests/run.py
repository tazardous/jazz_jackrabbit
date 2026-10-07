"""Play-test bot for Turbo Bunny Blast Run.
Plays every level at both difficulties (runs right at full speed, jumps pits, floats, zaps shellbots and the boss),
checks each level can be finished, a pit fall respawns, and runs a real-time keyboard session."""
import sys
from playwright.sync_api import sync_playwright
CH='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
URL='file://'+__file__.rsplit('/tests/',1)[0]+'/index.html'
BOT="""
window.bot=function(maxFrames){
  const D=__JJ,P=D.P,T=16; let frames=0,falls=0,lastX=-1,stuck=0,maxSpeed=0;
  const solid=c=>c==='#'||c==='G';
  while(frames<maxFrames&&D.state==='play'){
    frames++;
    const LV=D.LV, tile=(tx,ty)=>D.tileAt(tx,ty);
    D.down.right=true; D.down.left=false; let jump=false;
    const bs=LV.boss; if(bs&&bs.alive&&P.x>(LV.wall-12)*T){ D.down.right=false; D.down.left=false; if(bs.x+bs.w/2<P.x-30){ D.down.left=true; } else if(bs.x>P.x+30){ D.down.right=true; } P.face=(bs.x<P.x)?-1:1; D.hit.add('shoot'); }
    const look=Math.max(14,Math.abs(P.vx)*7), px=P.x+P.w;
    const gTx=Math.floor((px+look)/T); let ground=false; for(let r=LV.top;r<LV.H;r++) if(solid(tile(gTx,r))) ground=true;
    if(!ground) jump=true;
    for(let r=Math.floor((P.y)/T);r<=Math.floor((P.y+P.h-1)/T);r++) if(solid(tile(Math.floor((px+6)/T),r))) jump=true;
    for(const c of LV.crits) if(c.alive&&c.x>P.x&&c.x-P.x<60&&Math.abs(c.y-P.y)<40) D.hit.add('shoot');
    const b=LV.boss; if(b&&b.alive&&Math.abs(b.x-P.x)<200) D.hit.add('shoot');
    D.down.jump=false; if(jump&&P.ground){ D.hit.add('jump'); D.down.jump=true; } else if(!P.ground&&P.vy>1&&!ground) D.down.jump=true;
    D.step();
    maxSpeed=Math.max(maxSpeed,Math.abs(P.vx));
    if(P.inv===90) falls++;
    if(Math.abs(P.x-lastX)<0.01){ stuck++; } else stuck=0; lastX=P.x;
    if(stuck>500) return {fail:'stuck at x='+P.x+' tile '+Math.floor(P.x/T),frames};
  }
  D.down.right=false; D.down.jump=false;
  return {ok:D.state==='levelEnd',state:D.state,frames,falls,pops:D.LV.pops,carrots:D.LV.got,maxSpeed:+maxSpeed.toFixed(2)};
};
"""
fails=0
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=CH,args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
    pg=b.new_page(viewport={'width':900,'height':540}); errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('console',lambda m:errs.append(m.text) if m.type=='error' and 'Failed to load' not in m.text else None)
    pg.add_init_script('window.__JJmanual=true;'); pg.goto(URL); pg.wait_for_timeout(400); pg.evaluate(BOT+';0')
    for diff in (0,1):
        for i in range(5):
            pg.evaluate(f'__JJ.setDiff({diff});__JJ.startLevel({i});0')
            r=pg.evaluate('bot(30000)'); ok=r.get('ok'); fails+=0 if ok else 1
            print(('PASS' if ok else 'FAIL'),'diff',diff,'level',i+1,r)
    # fall respawn
    pg.evaluate('__JJ.startLevel(0);0'); pg.evaluate('__JJ.P.x=__JJ.LV.LEVELS?0:0;0')
    pg.evaluate('(()=>{const D=__JJ; const pit=D.LEVELS[0].pits[0][0]; D.P.x=(pit+1)*16-2; D.P.y=100; D.P.vy=0; for(let i=0;i<120;i++) D.step(); })();0')
    x=pg.evaluate('__JJ.P.x'); y=pg.evaluate('__JJ.P.y'); ok=pg.evaluate('__JJ.state')=='play' and y<200
    print('PASS' if ok else 'FAIL','fall respawn',x,y); fails+=0 if ok else 1
    # shooting kills a bot
    pg.evaluate('__JJ.startLevel(0);0')
    r=pg.evaluate('(()=>{const D=__JJ,c=D.LV.crits[0]; D.P.x=c.x-50; D.P.y=c.y-12; D.P.face=1; D.hit.add("shoot"); for(let i=0;i<40;i++){ D.step(); } return c.alive;})()')
    print('PASS' if r is False else 'FAIL','zap pops a shellbot'); fails+=0 if r is False else 1
    # real time keyboard
    pg.evaluate('window.__JJmanual=false;0'); pg.evaluate('__JJ.startLevel(0);0'); pg.wait_for_timeout(200)
    x0=pg.evaluate('__JJ.P.x'); pg.keyboard.down('ArrowRight'); pg.wait_for_timeout(1500); pg.keyboard.press('x'); pg.keyboard.up('ArrowRight'); x1=pg.evaluate('__JJ.P.x')
    print('PASS' if x1>x0+80 else 'FAIL','real-time keyboard',x0,'->',x1); fails+=0 if x1>x0+80 else 1
    print('PASS' if not errs else 'FAIL','no console errors',errs[:3]); fails+=1 if errs else 0
    b.close()
print('FAILS',fails); sys.exit(1 if fails else 0)
