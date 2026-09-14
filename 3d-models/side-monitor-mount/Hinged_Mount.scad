// V3. Millimetres. Assembly: X right, Y up, Z toward viewer.
// Print outputs selected with part. Assembly is inspection only.
part="holder"; // holder, wing, pivot_pin, index_pin, gauge, assembly
angle=0; // nominal -30..30 in 5-degree steps
$fn=72;
monitor=10; tape=1;
width=84; clearance=0.7; cheek=3.5; shell=3;
inner=width+2*clearance; left=-inner/2-cheek; right=inner/2+cheek;
ax=62; az=-(monitor+tape+13); // -24 nominal
profile=[[0,0],[61,0],[61,-8],[32,-49],[26,-50],[-3,-10]];
module prism_x(x,length){translate([x,0,0]) multmatrix([[0,0,1,0],[1,0,0,0],[0,1,0,0],[0,0,0,1]]) linear_extrude(length) children();}
module ycyl(x,y,z,h,r){translate([x,y,z]) rotate([-90,0,0]) cylinder(h=h,r=r);}
module pivot_rotate(a){translate([ax,0,az]) rotate([0,a,0]) translate([-ax,0,-az]) children();}
module cradle(){difference(){
 prism_x(left,inner+2*cheek) offset(delta=shell) polygon(profile);
 prism_x(-inner/2,inner) union(){offset(delta=clearance) polygon(profile);translate([-3-clearance,-0.1]) square([66,15]);}
 translate([-100,-20,0]) cube([200,120,30]);
 translate([-100,61+clearance,-80]) cube([200,30,110]);
 translate([-11,12,-70]) cube([22,65,57]);
}}
module hub(y,h){difference(){ycyl(ax,y,az,h,10);ycyl(ax,y-1,az,h+2,3.4);}}
module sector(){
 // Rear sector with alternating radii: no fine teeth or flexible tabs.
 difference(){
  union(){
   translate([ax,59.7,az]) rotate([-90,0,0]) linear_extrude(8.3)
    polygon(concat([for(a=[-35:1:35]) [56*sin(a),56*cos(a)]],[for(a=[35:-1:-35]) [23*sin(a),23*cos(a)]]));
   translate([ax-7,59.7,az-30]) cube([14,8.3,32]);
  }
  for(a=[-30:10:30]) ycyl(ax+50*sin(a),59,az-50*cos(a),10,2.4);
  for(a=[-25:10:25]) ycyl(ax+40*sin(a),59,az-40*cos(a),10,2.4);
  ycyl(ax,59,az,11,3.4);
  for(a=[-30:5:30]) let(r=(a%10==0 ? 54.1 : 34.5))
   translate([ax+r*sin(a),68.1,az-r*cos(a)]) rotate([90,0,0])
    linear_extrude(0.8) text(str(-a),size=2.2,halign="center",valign="center");
 }
}
module wing(){difference(){union(){
 // Adhesive face remains absolutely flat at Z=-11 (default).
 translate([ax+11,0,-monitor-tape-8]) cube([76,60,8]);
 // Rear reinforcing rails only.
 for(y=[5,49]) translate([ax+11,y,-monitor-tape-14]) cube([76,6,6.3]);
 for(y=[0,50]){
  hub(y,10);
  translate([ax, y, az-6]) cube([18,10,10]);
 }
 sector();
} ycyl(ax,-1,az,80,3.4);
}}
module holder(){difference(){union(){
 cradle();
 hub(10.7,38.6);
 translate([right-1,14,az-6]) cube([ax-right+2,32,12]);
 // Spine stays left of stationary upper hinge barrel.
 translate([right-1,26,az-6]) cube([4,47,12]);
 translate([right-1,68.7,az-6]) cube([ax-right+2,8,12]);
 hull(){ycyl(ax,68.7,az,8,7);ycyl(ax,68.7,az-52,8,7);}
 }
 ycyl(ax,9,az,70,3.4);
 for(r=[40,50]) ycyl(ax,68,az-r,10,2.4);
}}
module pin(d,L,head){
 // Print upright on head. Chamfered insertion end at top.
 cylinder(h=4,r=head/2);
 translate([0,0,3.8]) cylinder(h=L-0.8,r=d/2);
 translate([0,0,L+3]) cylinder(h=1,r1=d/2,r2=d/2-0.7);
}
module gauge(){intersection(){cradle();translate([left-0.1,-10,-70]) cube([10.6,85,90]);}}
if(part=="holder") translate([0,0,-left]) rotate([0,-90,0]) holder();
if(part=="wing") translate([0,0,-ax+56*sin(35)]) rotate([0,-90,0]) wing();
if(part=="pivot_pin") pin(6,78,14);
if(part=="index_pin") pin(4,18,10);
if(part=="gauge") translate([0,0,-left]) rotate([0,-90,0]) gauge();
if(part=="assembly"){
 color("SteelBlue") wing();
 color("DarkSlateGray") pivot_rotate(angle) holder();
}

if(part=="coupon") difference(){cube([32,16,16]);translate([9,-1,8]) rotate([-90,0,0]) cylinder(h=18,r=3.4);translate([24,-1,8]) rotate([-90,0,0]) cylinder(h=18,r=2.4);}
