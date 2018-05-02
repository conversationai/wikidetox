/*jslint vars: true, plusplus: true, devel: true, nomen: true, indent: 4, maxerr: 50 */
/*global require, define,THREE, brackets: true, $, window, navigator , clearInterval , setInterval,TWEEN, d3*/

define(function () {

    "use strict";

    var sphereFunctions = {

        randomSpherePoint: function (x0, y0, z0, radius) {
            var u = Math.random();
            var v = Math.random();
            var theta = 2 * Math.PI * u;
            var phi = Math.acos(2 * v - 1);
            var x = x0 + (radius * Math.sin(phi) * Math.cos(theta));
            var y = y0 + (radius * Math.sin(phi) * Math.sin(theta));
            var z = z0 + (radius * Math.cos(phi));

            return {
                x: x,
                y: y,
                z: z
            };
        },
        diatanceTo: function (a, b) {

            var dx = a.x - b.x;
            var dy = a.y - b.y;
            var dz = a.z - b.z;

            return Math.sqrt(dx * dx + dy * dy + dz * dz);
        }
    };

    return sphereFunctions;


});
