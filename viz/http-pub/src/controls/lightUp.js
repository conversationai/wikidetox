/*jslint vars: true, plusplus: true, devel: true, nomen: true, indent: 4, maxerr: 50 */
/*global require, d3, THREE, define, brackets: true, $, window */

define(['three'], function (THREE) {
    "use strict";


    var LightUp = function (s, container, gui) {

        var scene = s;

        this.lights = [];

        this.gui = gui;

        function handleColorChange(color) {
            return function (value) {
                if (typeof value === "string") {
                    value = value.replace('#', '0x');
                }
                color.setHex(value);
            };
        }
        function random(min, max) {
            return Math.floor(Math.random() * (max - min + 1)) + min;
        }

        this.addAmbientLight = function (color) {
            var light = new THREE.AmbientLight(color);
            scene.add(light);
            return light;
        };
        this.addDirectionalLight = function (color, intensity, pos) {
            var light = new THREE.DirectionalLight(color, intensity);
            light.position.set(pos.x, pos.y, pos.z);
            light.helper = new THREE.DirectionalLightHelper(light, 200);

            scene.add(light);
            scene.add(light.helper);
            light.helper.visible = false;
            return light;
        };
        this.addHemisphereLight = function (skyColorHex, groundColorHex, intensity, pos) {
            var light = new THREE.HemisphereLight(skyColorHex, groundColorHex, intensity);
            var hemisphereLightHelper = new THREE.HemisphereLightHelper(light, 200);
            light.helper = hemisphereLightHelper;
            light.position.set(pos.x, pos.y, pos.z);
            scene.add(light);
            scene.add(light.helper);
            light.helper.visible = false;
            return light;
        };
        this.addPointLight = function (hex, intensity, distance, decay, pos) {
            var light = new THREE.PointLight(hex, intensity, distance, decay);
            light.position.set(pos.x, pos.y, pos.z);
            var pointLightHelper = new THREE.PointLightHelper(light, 1);
            light.helper = pointLightHelper;

            scene.add(light);
            scene.add(light.helper);
            light.helper.visible = false;
            return light;
        };

        this.addSpotLight = function (color, pos, castShadow) {
            var light = new THREE.SpotLight(0xffffff);
            light.position.set(pos.x, pos.y, pos.z);

            light.castShadow = castShadow;

            light.shadowMapWidth = 1024;
            light.shadowMapHeight = 1024;

            light.shadowCameraNear = 500;
            light.shadowCameraFar = 4000;
            light.shadowCameraFov = 30;

            var spotLightHelper = new THREE.SpotLightHelper(light);
            light.helper = spotLightHelper;

            scene.add(light);
            scene.add(light.helper);
            light.helper.visible = false;
            return light;
        };
        if (this.gui) {

        }

        this.lightsNumber = {};

        var addedLights = null;
        if (this.gui) {
            addedLights = gui.addFolder("Lights");
        }

        this.addGuiControls = function (light, option) {

            if (!this.gui) {
                return;
            }

            if (this.lightsNumber[option.name]) {
                this.lightsNumber[option.name] += 1;
            } else {
                this.lightsNumber[option.name] = 1;
            }

            light.name = option.name + '_' + this.lightsNumber[option.name];

            var guiControl = addedLights.addFolder(light.name);
            guiControl.add(light, 'name').name('Light name');


            option.colors.forEach(function (color) {
                var colorControl = {};
                colorControl[color.name] = color.colorRef.getHex();
                guiControl.addColor(colorControl, color.name).onChange(handleColorChange(color.colorRef));
            });

            var intensity = guiControl.add(light, 'intensity', 0, 1);
            if (option.intensity === false) {
                guiControl.remove(intensity);
            }

            var visible = guiControl.add(light, 'visible');
            if (option.visible === false) {
                guiControl.remove(visible);
            }


            var x = guiControl.add(light.position, 'x', -2000, 2000).step(1),
                y = guiControl.add(light.position, 'y', -2000, 2000).step(1),
                z = guiControl.add(light.position, 'z', -2000, 2000).step(1);

            if (option.position === false) {
                guiControl.remove(x);
                guiControl.remove(y);
                guiControl.remove(z);
            }

            guiControl.add(light.helper, 'visible').name('Show Helper');

            guiControl.add({
                delete: function () {
                    scene.remove(light);
                    scene.remove(light.helper);
                    addedLights.removeFolder(light.name);
                }
            }, 'delete').name('Delete');

        };

        this.addLight = function (name) {

            var light = null;

            switch (name) {

                case 'HemisphereLight':
                    light = this.addHemisphereLight(0xffffff, 0x7d6464, 0.8, {
                        x: 0,
                        y: 1,
                        z: 0
                    });
                    this.addGuiControls(light, {
                        name: name,
                        colors: [{
                            colorRef: light.color,
                            name: 'color'
                        }, {
                            colorRef: light.groundColor,
                            name: 'groundColor'
                        }]
                    });
                    light.position.x = random(0, 10);
                    light.helper.visible = true;
                    this.lights.push(light);
                    break;
                case 'DirectionalLight':
                    light = this.addDirectionalLight(0xffffff, 0.5, {
                        x: 0,
                        y: 0,
                        z: 1
                    });
                    this.addGuiControls(light, {
                        name: name,
                        colors: [{
                            colorRef: light.color,
                            name: 'color'
                        }]
                    });
                    light.helper.visible = true;
                    this.lights.push(light);
                    break;
            }


        };

        this.addLightsInsertInterface = function () {
            var that = this;
            var addLights = gui.addFolder("Add lights");
            var selected = {
                lightType: 'DirectionalLight'
            };
            addLights.add(selected, 'lightType', ['DirectionalLight', 'HemisphereLight']).name('Choose light');
            addLights.add({
                add: function () {
                    that.addLight(selected.lightType);
                }
            }, 'add').name('Add light');
        };
        if (this.gui) {
            this.addLightsInsertInterface();
        }



    };

    return LightUp;
});
