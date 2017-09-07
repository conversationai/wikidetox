
define(['three', './controls/lightUp', '../../libs/OBJLoader'], function (THREE, LightUp) {


    var manager = new THREE.LoadingManager();
    manager.onProgress = function (item, loaded, total) {

    };
    var texture = new THREE.Texture();

    var loader = new THREE.OBJLoader(manager);

    var iconColor = {
        toxic: 0xFF0000,
        nonToxic: 0x737373
    }
    var iconShape = {
        toxic: 'shape001.obj',
        nonToxic: 'shape002.obj'
    };
    var onProgress = function (xhr) {
        if (xhr.lengthComputable) {
            var percentComplete = xhr.loaded / xhr.total * 100;
        }
    };
    var onError = function (xhr) {
    };

    var iconReference = {
        nonToxic: null,
        toxic: null
    };

    function loadIcon(iconObjShape, iconHexColor, objRef) {
        loader.load('./images/shapes/' + iconObjShape, function (object) {
            // object.traverse(function (child) {
            //     if (child instanceof THREE.Mesh) {
            //         child.material.map = texture;
            //     }
            // });
            object.traverse(function (child) {
                if (child instanceof THREE.Mesh) {
                    //child.material.ambient.setHex(0xFF0000);
                    child.material.color.setHex(iconHexColor);
                    child.material.transparent = true;
                }
            });

            iconReference[objRef] = object;
            console.log(iconReference)

        }, onProgress, onError);
    }

    loadIcon(iconShape['toxic'], iconColor['toxic'], 'toxic');
    loadIcon(iconShape['nonToxic'], iconColor['nonToxic'], 'nonToxic');

    function isLoaded(cb) {
        if (iconReference.nonToxic && iconReference.toxic) {
            cb();
        } else {
            setTimeout(() => {
                isLoaded(cb);
            }, 10)
        }
    }
    return function (ele, icon) {
        console.log(ele);
        var container;
        var camera, scene, renderer;
        var mouseX = 0, mouseY = 0;
        var width = 70;
        var height = 70;
        var windowHalfX = width / 2;
        var windowHalfY = height / 2;

        var object3d = null,
            lightMe;


        function init(ele, icon) {

            container = $('<div/>').addClass('icons3d')[0];

            camera = new THREE.PerspectiveCamera(45, width / height, 1, 2000);
            camera.position.z = 50;
            // scene
            scene = new THREE.Scene();

            lightMe = new LightUp(scene, container);
            lightMe.addHemisphereLight(0xffffff, 0x7d6464, 0.650999283900787, {
                x: 0,
                y: 1,
                z: 0
            });
            lightMe.addHemisphereLight(0xffffff, 0x7d6464, 0.2806031396124082, {
                x: -2000,
                y: 1,
                z: 0
            });
            lightMe.addDirectionalLight(0xffffff, 0.15, {
                x: 0,
                y: -384,
                z: 400
            });

            object3d = iconReference[icon].clone().children[0];
            object3d.position.y = 0;
            var scaleValue = 20;
            object3d.scale.x = scaleValue;
            object3d.scale.y = scaleValue;
            object3d.scale.z = scaleValue;
            scene.add(object3d);

            //
            renderer = new THREE.WebGLRenderer({
                antialias: true,
                alpha: true
            });
            renderer.setClearColor(0x000000, 0);
            renderer.setPixelRatio(window.devicePixelRatio);
            renderer.setSize(width, height);

            container.append(renderer.domElement);

            $(function () {
                $(ele).append(container);
            });
        }
        function animate() {
            requestAnimationFrame(animate);
            render();

            if (object3d) {
                object3d.rotation.y += Math.random() / 100;
                object3d.rotation.x += Math.random() / 100;
                object3d.rotation.z += Math.random() / 100;
            }
        }
        function render() {
            camera.lookAt(scene.position);
            renderer.render(scene, camera);
        }

        isLoaded(function () {
            init(ele, icon);
            animate();
        });

    }


});
