module buttonrow() {
    for (i = [0 : 8]) {
        translate([ i*(12+1), 0, 0 ]) square(12);
    }
}

translate([0,0,0]) buttonrow();

translate([0,12+1,0]) buttonrow();
