"""Render the actual companion code at native button resolution."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PIL import Image, ImageDraw
from ocdeck.jelly import Jelly, DeckGeometry
from ocdeck.jelly_smooth import TRICKS

def main():
    names = ['hello','cookie','pizza','donut','pogo','rainbow']
    pets = [Jelly(DeckGeometry(), i, options={'thoughts':'off'}) for i in range(6)]
    for pet,name in zip(pets,names):
        pet.settle(0,0)
        pet.play(name,0)
    frames=[]
    for frame in range(48):
        t=frame/15
        canvas=Image.new('RGB',(280,194),'#101823')
        d=ImageDraw.Draw(canvas)
        for i,pet in enumerate(pets):
            pet.now=t
            tile=pet.crops({0})[0]
            x,y=8+(i%3)*92,8+(i//3)*94
            canvas.paste(tile,(x,y),tile)
            d.text((x+4,y+80),names[i],fill='white')
        frames.append(canvas.quantize(colors=48))
    out=Path('docs/jelly/jelly_refined.gif')
    frames[0].save(out,save_all=True,append_images=frames[1:],duration=67,loop=0)
    frames[20].save('docs/jelly/jelly_refined.png')
if __name__=='__main__': main()
