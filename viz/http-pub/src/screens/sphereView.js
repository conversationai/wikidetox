/*jslint vars: true, plusplus: true, devel: true, nomen: true, indent: 4, maxerr: 50 */
/*global require, define,THREE, brackets: true, $, window, navigator , clearInterval , setInterval, d3, Float32Array */

define(['three', './toxicObject', '../sphereFunction'], function (THREE, ToxicParticle, SphereFunction) {

    "use strict";

    return function (scene, gui, listiner) {

        var that = this;

        this.getParticleSystem = function (particles, particlesNumber) {

            var positions = new Float32Array(particlesNumber * 3);
            var colors = new Float32Array(particlesNumber * 3);
            var sizes = new Float32Array(particlesNumber);
            var textures = new Float32Array(particlesNumber);
            var color = new THREE.Color('#000000');

            var uniforms = {
                amplitude: {
                    type: "f",
                    value: 1.0
                },
                color: {
                    type: "c",
                    value: new THREE.Color("#FFFFFF")
                }
            };

            for (var j = 0, i3 = 0; j < particlesNumber; j++ , i3 += 3) {

                var spherepoint = SphereFunction.randomSpherePoint(0, 0, 0, 1000);
                positions[i3 + 0] = spherepoint.x;
                positions[i3 + 1] = spherepoint.y;
                positions[i3 + 2] = spherepoint.z;

                sizes[j] = 4;

                textures[j] = 0;

                colors[i3 + 0] = color.r;
                colors[i3 + 1] = color.g;
                colors[i3 + 2] = color.b;

            }

            uniforms.texture0 = {
                type: "t",
                value: new THREE.TextureLoader().load("./images/shape0.png")
            };

            var vertexShader = [
                "uniform float amplitude;",
                "attribute float size;",
                "attribute float textureNo;",
                "attribute vec3 customColor;",
                "varying vec3 vColor;",
                "varying float tShape;",
                "void main() {",
                "vColor = customColor;",
                "tShape = textureNo;",
                "vec4 mvPosition = modelViewMatrix * vec4( position, 1.0 );",
                "gl_PointSize = size * ( 300.0 / length( mvPosition.xyz ) );",
                "gl_Position = projectionMatrix * mvPosition;",
                "}"
            ].join("\n"),

                fragmentShader = [
                    "uniform vec3 color;",
                    "uniform sampler2D texture0;",
                    "varying vec3 vColor;",
                    "varying float tShape;",
                    "void main() {",
                    "gl_FragColor = vec4( color * vColor, 1.0 );",
                    "if(int(tShape) == 0) gl_FragColor = gl_FragColor * texture2D( texture0, gl_PointCoord );",
                    "}"
                ].join("\n");

            var shaderMaterial = new THREE.ShaderMaterial({
                uniforms: uniforms,
                vertexShader: vertexShader,
                fragmentShader: fragmentShader,
                blending: THREE.NormalBlending,
                depthTest: false,
                transparent: true
            });

            // particles.colors = colors;
            particles.addAttribute('position', new THREE.BufferAttribute(positions, 3));
            particles.addAttribute('customColor', new THREE.BufferAttribute(colors, 3));
            particles.addAttribute('size', new THREE.BufferAttribute(sizes, 1));
            particles.addAttribute('textureNo', new THREE.BufferAttribute(textures, 1));

            return new THREE.Points(particles, shaderMaterial);;

        }

        this.generateParticles = function (data, animate, cb) {


            var scene = animate.scene;

            var dataNumbers = {};
            dataNumbers.reverted = 0;
            this.particlesNumber = Number(data.nonToxicCount);
            var toxicComments = data.toxicComments;
            var toxicCommentsCount = toxicComments.length

            for (var i = 0; i < toxicCommentsCount; i++) {
                that.toxicParticle.add(toxicComments[i].attack, toxicComments[i].is_reverted, toxicComments[i].revision_id, i);
                if (toxicComments[i].is_reverted) {
                    dataNumbers.reverted += 1;
                }
            }

            //since we are not having any intraction on non-toxic comment , reduce the number of particles renderd to improve perfomance by particleDensity( 0 to 1)
            var particleDensity = 0.7;
            var particlesNumber = Math.floor(this.particlesNumber * particleDensity);

            this.particleSystem = this.getParticleSystem(this.particles, this.particlesNumber);

            //particleSystem.sortParticles = true;
            this.particleSystem.rotationSpeed = 0.00011;
            this.particleSystem.rotationFriction = 0.0001;
            //particleSystem.dynamic = true;

            scene.add(this.particleSystem);
            scene.add(that.toxicParticle.toxicObjects);


            cb(dataNumbers);
        }


        this.addGuiParams = function (data) {

            var particleLen = this.particlesNumber;
            var sizes = this.particles.attributes.size.array;
            var colors = this.particles.attributes.customColor.array;
            var particleSystem = this.particleSystem;

            var guiControl = this.gui.addFolder("Particle Params");
            var updateParams = {
                name: "Particle Params",
                color: '#000000',
                size: 4,
                rotationSpeed: 0.011,
                rotationFriction: 0.00005
            };
            particleSystem.rotationSpeed = updateParams.rotationSpeed;
            particleSystem.rotationFriction = updateParams.rotationFriction;

            var colorControl = guiControl.addColor(updateParams, 'color'),
                sizeControl = guiControl.add(updateParams, 'size', 1, 50);

            var color = new THREE.Color();
            colorControl.onChange(function () {
                for (var i = 0, i3 = 0; i < particleLen; i++ , i3 += 3) {
                    color.setStyle(updateParams.color);
                    colors[i3 + 0] = color.r;
                    colors[i3 + 1] = color.g;
                    colors[i3 + 2] = color.b;
                }
            });
            sizeControl.onChange(function () {
                for (var i = 0, i3 = 0; i < particleLen; i++ , i3 += 3) {
                    sizes[i] = updateParams.size;
                }
            });

            var rotationControl = guiControl.add(updateParams, 'rotationSpeed', 0, 0.05);
            rotationControl.onChange(function () {
                particleSystem.rotationSpeed = updateParams.rotationSpeed;
            });

            var rotationFriction = guiControl.add(updateParams, 'rotationFriction', 0, 0.005);
            rotationFriction.onChange(function () {
                particleSystem.rotationFriction = updateParams.rotationFriction;
            });

            gui.add({
                copy: function () {
                    gui.saveCurrentValues();
                }
            }, 'copy').name('Copy Values');

        };

        this.renderUpdates = function () {

            if (!that.initialized) {
                return true;
            }

            if (that.spin) {
                that.particleSystem.rotation.y += that.particleSystem.rotationSpeed;
                that.toxicParticle.toxicObjects.rotation.y += that.particleSystem.rotationSpeed;

                if (that.particleSystem.rotationSpeed > 0) {
                    that.particleSystem.rotationSpeed -= that.particleSystem.rotationFriction;
                } else {
                    that.particleSystem.rotationSpeed = 0;
                }
            }

            //remove after gui edit

            that.particles.attributes.size.needsUpdate = true;
            that.particles.attributes.customColor.needsUpdate = true;

            that.toxicParticle.renderUpdates();

        };

        this.stopSpin = function () {
            this.spin = false;
        };

        this.startSpin = function () {
            this.spin = true;
        };

        this.screenInit = function () {
            this.initialized = true;
        };

        this.init = function (data, cb) {

            this.initialized = false;

            this.gui = gui;
            this.toxicParticle = new ToxicParticle(scene, this.gui, listiner);

            this.particleSystem;
            this.particles = new THREE.BufferGeometry();
            this.spin = true;
            this.scene = scene;
            this.particlesNumber = 0;

            this.generateParticles(data, scene, cb);
            that.addGuiParams(data);
        };


    };

});
