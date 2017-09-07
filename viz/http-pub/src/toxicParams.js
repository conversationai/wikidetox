/*jslint vars: true, plusplus: true, devel: true, nomen: true, indent: 4, maxerr: 50 */
/*global require, define, THREE, brackets: true */

define(['three'], function (THREE) {


    function toxicParams() {

        var that = this;

        this.minRotationValue = 0.00;
        this.maxRotationVaue = 0.027571937943287817;
        this.minSizeValue = 10;
        this.maxSizeValue = 69.78647078091444;

        this.minToxicValue = 0.50;
        this.maxToxicValue = 1;


        this.scaleBetween = function (unscaledNum, minAllowed, maxAllowed, min, max) {
            return (maxAllowed - minAllowed) * (unscaledNum - min) / (max - min) + minAllowed;
        };

        this.getToxicRotationParams = function (toxicValue) {
            return this.scaleBetween(toxicValue, this.minRotationValue, this.maxRotationVaue, this.minToxicValue, this.maxToxicValue);
        };

        this.getToxicSizeValue = function (toxicValue) {
            return this.scaleBetween(toxicValue, this.minSizeValue, this.maxSizeValue, this.minToxicValue, this.maxToxicValue);
        };

        this.addGuiControls = function (gui, objects) {
            var guiControl = gui.addFolder("Toxic Params");
            var updateToxicParams = {
                maxRotationVaue: 0.01,
                maxSizeValue: 50,
                color: "#FF0000"
            };
            var rotationControl = guiControl.add(updateToxicParams, 'maxRotationVaue', 0, 0.50),
                sizeControl = guiControl.add(updateToxicParams, 'maxSizeValue', 1, 100);

            rotationControl.onChange(function () {
                objects.children.forEach(function (obj) {
                    obj.rotationThreshold = that.scaleBetween(obj.toxicMeasure, that.minRotationValue, updateToxicParams.maxRotationVaue, that.minToxicValue, that.maxToxicValue);
                });
            });

            sizeControl.onChange(function () {
                objects.children.forEach(function (obj) {
                    var scaleValue = that.scaleBetween(obj.toxicMeasure, that.minSizeValue, updateToxicParams.maxSizeValue, that.minToxicValue, that.maxToxicValue);
                    obj.scale.x = scaleValue;
                    obj.scale.y = scaleValue;
                    obj.scale.z = scaleValue;
                });
            });

            var colorControl = guiControl.addColor(updateToxicParams, 'color');
            colorControl.onChange(function () {
                objects.children.forEach(function (obj) {
                    obj.traverse(function (child) {
                        if (child instanceof THREE.Mesh) {
                            child.material.color.setStyle(updateToxicParams.color);
                        }
                    });
                });
            });

        };

    }


    return toxicParams;

});
