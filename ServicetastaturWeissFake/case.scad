module buttonrow() {
    for (i = [0 : 7]) {
        translate([ i*(12.1+5.7), 0, 0 ]) square(12);
    }
}

module buttonshape() {
translate([0,0,0]) buttonrow();
translate([0,12.1+3.24,0]) buttonrow();
}



difference(){translate([-2,-1.5,0])cube([140,30,2]);linear_extrude(2) buttonshape();}