"""Offline comparison with fixed layout/seed/scene and equal simulated duration."""
from pathlib import Path
import json
import statistics
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ocdeck.jelly import Jelly, DeckGeometry
from ocdeck.world import World
from ocdeck.world_settings import settings
from ocdeck.world_weather import WeatherService

report=[]
for size,rows,cols in ((72,2,3),(80,3,5),(96,4,8)):
    for enabled in (False,True):
        o=settings(dict(living_world=enabled,scene_override='autumn_rake',weather=False,auto_location=False,captions=False))
        w=World(o,WeatherService(o))
        j=Jelly(DeckGeometry(rows,cols,size,size),seed=6,options={'thoughts':'off','needs':False})
        j.settle(0,0)
        free=set(range(rows*cols))
        samples=[]
        cold=None
        for i in range(600):
            t=i/24
            start=time.perf_counter()
            j.update(t,free)
            w.tick(t,j,free)
            w.decorate(t,j,j.crops(free),free)
            ms=(time.perf_counter()-start)*1000
            if i==0:cold=ms
            if i>=60:samples.append(ms)
        report.append(dict(size=size,keys=rows*cols,living_world=enabled,first_frame_ms=cold,median_ms=statistics.median(samples),mean_ms=statistics.mean(samples),p95_ms=sorted(samples)[int(len(samples)*.95)]))
path=Path(__file__).resolve().parents[1]/'docs/jelly/living-previews/comparison.json'
path.write_text(json.dumps({'method':'600 frames at 24Hz simulated time; first 60 excluded from warm statistics; seed 6; all keys free; same scene, different activity poses; CPU offline composition only. First frame is not isolated-process cold-cache measurement.','results':report},indent=2)+'\n')
print(json.dumps(report,indent=2))
