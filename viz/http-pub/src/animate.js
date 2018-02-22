/*jslint vars: true, plusplus: true, devel: true, nomen: true, indent: 4, maxerr: 50 */
/*global require, define,THREE, brackets: true, $, window, navigator , clearInterval , setInterval, requestAnimationFrame*/

define(['three', './controls/lightUp', '../libs/THREETrackBall', '../libs/stats', '../libs/tween',], function (THREE, LightUp) {

    "use strict";

    var stats,
        camera, scene, renderer, containerEle,
        mouse = new THREE.Vector2(),
        controls,
        clock = new THREE.Clock(),
        renderUpdates = [],
        lightMe,
        renderFunctions,
        renderId = null;

    function initlizeSharedResources() {
        stats = null;
        camera = null;
        scene = null;
        renderer = null;
        containerEle = null;
        mouse = new THREE.Vector2();
        controls = null;
        clock = new THREE.Clock();
        renderUpdates = [];
        lightMe = null;
        renderFunctions = null;


        if (renderId) {
            cancelAnimationFrame(renderId);
        }
    }

    function animationInit(canvas, gui) {

        initlizeSharedResources();

        containerEle = $(canvas);

        //set camera
        camera = new THREE.PerspectiveCamera(40, containerEle.innerWidth() / containerEle.innerHeight(), 1, 100000);
        camera.position.z = 4500;
        camera.position.x = 1000;

        // RENDERER

        renderer = new THREE.WebGLRenderer({
            antialias: true,
            alpha: true
        });
        renderer.setClearColor(0x000000, 0);

        renderer.setSize(containerEle.innerWidth(), containerEle.innerHeight());
        renderer.domElement.style.position = 'absolute';
        containerEle.append(renderer.domElement);


        controls = new THREE.TrackballControls(camera, renderer.domElement);
        controls.noPan = true;
        controls.rotateSpeed = 0.5;
        controls.zoomSpeed = 0.5;
        controls.minDistance = 0;
        controls.maxDistance = 6000;

        scene = new THREE.Scene();
        //scene.fog = new THREE.Fog(0xffffff, 1000, 10000);


        lightMe = new LightUp(scene, containerEle, gui);


        stats = new Stats();
        stats.domElement.style.position = 'absolute';
        stats.domElement.style.top = '0px';
        stats.domElement.id = 'stats';
        containerEle.append(stats.domElement);

        var axes = new THREE.AxisHelper(1000);
        //scene.add(axes);

        //
        window.addEventListener('resize', onWindowResize, false);

        function setMobileSphereZoom(width) {
            if (width < 450) {
                camera.position.z = 6000;
            } else {
                camera.position.z = 4500;
            }
        }

        function onWindowResize() {
            camera.aspect = containerEle.innerWidth() / containerEle.innerHeight();
            camera.updateProjectionMatrix();
            renderer.setSize(containerEle.innerWidth(), containerEle.innerHeight());
            setMobileSphereZoom(containerEle.innerWidth());
        }

        onWindowResize();
    }


    var setScreenLighting = function () {

        var hemisphereLight = lightMe.addHemisphereLight(0xffffff, 0x7d6464, 0.650999283900787, {
            x: 0,
            y: 1,
            z: 0
        });

        lightMe.addGuiControls(hemisphereLight, {
            name: 'HemisphereLight',
            colors: [{
                colorRef: hemisphereLight.color,
                name: 'color'
            }, {
                colorRef: hemisphereLight.groundColor,
                name: 'groundColor'
            }]
        });
        lightMe.lights.push(hemisphereLight);


        var hemisphereLight2 = lightMe.addHemisphereLight(0xffffff, 0x7d6464, 0.2806031396124082, {
            x: -2000,
            y: 1,
            z: 0
        });

        lightMe.addGuiControls(hemisphereLight2, {
            name: 'HemisphereLight',
            colors: [{
                colorRef: hemisphereLight.color,
                name: 'color'
            }, {
                colorRef: hemisphereLight.groundColor,
                name: 'groundColor'
            }]
        });
        lightMe.lights.push(hemisphereLight2);

        var directionalLight = lightMe.addDirectionalLight(0xffffff, 0.25, {
            x: 0,
            y: -384,
            z: 400
        });
        lightMe.addGuiControls(directionalLight, {
            name: 'DirectionalLight',
            colors: [{
                colorRef: directionalLight.color,
                name: 'color'
            }]
        });
        lightMe.lights.push(directionalLight);

        var directionalLight1 = lightMe.addDirectionalLight(0xffffff, 0.25, {
            x: 20,
            y: 400,
            z: 20
        });
        lightMe.addGuiControls(directionalLight1, {
            name: 'DirectionalLight',
            colors: [{
                colorRef: directionalLight1.color,
                name: 'color'
            }]
        });
        lightMe.lights.push(directionalLight1);

        var directionalLight2 = lightMe.addDirectionalLight(0xffffff, 0.25, {
            x: 245,
            y: -114,
            z: -150
        });
        lightMe.addGuiControls(directionalLight2, {
            name: 'DirectionalLight',
            colors: [{
                colorRef: directionalLight2.color,
                name: 'color'
            }]
        });
        lightMe.lights.push(directionalLight2);

    };


    function animate() {
        renderId = requestAnimationFrame(animate);
        render();
        updatesScreenParams();
    }

    function render() {
        renderer.render(scene, camera);

        if (renderFunctions && renderFunctions.length) {
            renderFunctions.forEach(function (fns) {
                fns();
            });
        }
    }

    function updatesScreenParams() {
        stats.update();
        controls.update();
        TWEEN.update();
    }

    function startAnimation(renderUpdates) {
        renderFunctions = renderUpdates;
        animate();
    }

    function destroy() {

    }

    return function (canvas, gui) {
        animationInit(canvas, gui);

        this.scene = scene;
        this.camera = camera;
        this.renderer = renderer;
        this.renderUpdates = [];
        this.containerEle = containerEle;
        this.controls = controls;

        this.setScreenLighting = setScreenLighting;

        startAnimation(this.renderUpdates);

    };


});
