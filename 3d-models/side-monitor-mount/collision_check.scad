use <Hinged_Mount.scad>
for(a=[-30:5:30]) translate([a*300,0,0]) intersection(){wing();pivot_rotate(a) holder();}
