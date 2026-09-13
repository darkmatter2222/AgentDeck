"""Side-by-side original identity, restored pixel art, tiny wave, and live travel."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image, ImageDraw
from ocdeck.jelly import Jelly, DeckGeometry
from ocdeck.jelly_art import sprite

def main():
    pets = [Jelly(DeckGeometry(), i, options={'thoughts':'off','mood_colors':False}) for i in range(3)]
    for pet in pets:
        pet.settle(0,0)
        pet.deadline=100
    travel = Jelly(DeckGeometry(1,3),7,options={'thoughts':'off','mood_colors':False})
    travel.settle(0,0)
    frames=[]
    for frame in range(144):
        now=frame/24
        canvas=Image.new('RGB',(280,204),'#101823'); d=ImageDraw.Draw(canvas)
        for i,label in enumerate(('Original','Restored','Little wave')):
            x=8+i*92
            d.text((x,4),label,fill='white')
            if i==0:
                tile=Image.new('RGBA',(80,80));tile.paste(sprite(),(0,9))
            else:
                pet=pets[i];pet.now=now;pet.gesture='wave' if i==2 else ''
                tile=pet.crops({0})[0]
            canvas.paste(tile,(x,20),tile)
        if travel.state != 'hop':
            destination={0:1,1:2,2:1}[travel.current]
            travel.hop(destination,now,{0,1,2})
        travel.update(now,{0,1,2})
        for key,tile in travel.crops({0,1,2}).items():
            canvas.paste(tile,(8+key*88,118),tile)
        d.text((8,108),'Squash / stretch / land / wobble',fill='white')
        frames.append(canvas.quantize(colors=48))
    out=Path('docs/jelly/jelly_pixel_return.gif')
    frames[0].save(out,save_all=True,append_images=frames[1:],duration=42,loop=0)
    frames[40].resize((840,612),Image.Resampling.NEAREST).save('docs/jelly/jelly_pixel_return.png')
if __name__=='__main__':main()
