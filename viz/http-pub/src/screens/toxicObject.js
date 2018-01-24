/*jslint vars: true, plusplus: true, devel: true, nomen: true, indent: 4, maxerr: 50 */
/*global require, define,THREE, brackets: true, $, window, navigator , TWEEN , setTimeout*/

define(['three', '../sphereFunction', '../toxicParams', '../../libs/OBJLoader'], function (THREE, SphereFunction, ToxicParams) {


    function randomInt(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }

    function toxicParticle(animate, gui, listiner) {

        var that = this;

        var raycaster = new THREE.Raycaster(),
            mouse = new THREE.Vector2(-5000, -5000),
            INTERSECTED;

        this.toxicParamsGenerator = new ToxicParams();

        this.toxicObject = null;

        this.revertedObject = null;

        this.animate = animate;

        this.scene = animate.scene;

        this.selectedElement = null;
        this.selectedElementIndex = null;

        this.toAdd = [];

        this.inZoomAnimation = false;

        this.add = function (data, is_reverted, revid, i) {
            if (!this.toxicObject) {
                this.toAdd.push([data, is_reverted, revid, i]);
            } else {
                this.addObjectToScene(data, is_reverted, revid, i);
            }
        };

        this.toxicObjects = new THREE.Object3D();

        this.addObjectToScene = function (toxicMeasure, is_reverted, revid, index) {

            var newObject = null;

            if (is_reverted) {
                newObject = this.revertedObject.clone().children[0];
            } else {
                newObject = this.toxicObject.clone().children[0];
            }

            var currentLength = this.toxicObjects.children.length;


            var bestPosition = null;
            //itrate and get the best point
            if (currentLength > 0) {

                for (var j = 0; j < 10; j++) {
                    var maxDis = null;
                    var newPos = SphereFunction.randomSpherePoint(0, 0, 0, 1000);

                    for (var i = 0; i < currentLength - 1; i++) {
                        var objPos = this.toxicObjects.children[i].position;
                        var distance = SphereFunction.diatanceTo(objPos, newPos);
                        if (maxDis === null || maxDis > distance) {
                            maxDis = distance;
                        }
                    }
                    if (bestPosition === null || bestPosition[0] < maxDis) {
                        bestPosition = [maxDis, newPos];
                    }
                }
            } else {
                bestPosition = [null, SphereFunction.randomSpherePoint(0, 0, 0, 1000)];
            }

            newObject.toxicMeasure = toxicMeasure;

            newObject.position.x = bestPosition[1].x;
            newObject.position.y = bestPosition[1].y;
            newObject.position.z = bestPosition[1].z;

            var scaleValue = this.toxicParamsGenerator.getToxicSizeValue(toxicMeasure);
            newObject.scale.x = scaleValue;
            newObject.scale.y = scaleValue;
            newObject.scale.z = scaleValue;
            newObject.rotationThreshold = this.toxicParamsGenerator.getToxicRotationParams(toxicMeasure);
            newObject.updateMatrixWorld();
            newObject.indexId = index;
            newObject.revid = revid;
            newObject.ramdomRotationAxis = ['x', 'y', 'z'][randomInt(0, 2)];

            this.toxicObjects.add(newObject);
        };


        this.addFromList = function () {
            var that = this;
            this.toAdd.forEach(function (data) {
                that.addObjectToScene(data[0], data[1], data[2], data[3]);
            });
        };

        this.addCommentsData = function (data) {
            this.commmentsData = data;
        };

        this.load3dObj = function () {
            var that = this;
            var loader = new THREE.OBJLoader();

            loader.load('./images/shapes/shape001.obj', function (object) {
                object.traverse(function (child) {
                    if (child instanceof THREE.Mesh) {
                        //child.material.ambient.setHex(0xFF0000);
                        child.material.color.setHex(0xFF0000);
                        child.material.transparent = true;
                    }
                });
                that.toxicObject = object;
                loader.load('./images/shapes/shape002.obj', function (object) {
                    object.traverse(function (child) {
                        if (child instanceof THREE.Mesh) {
                            //child.material.ambient.setHex(0xFF0000);
                            child.material.color.setHex(0x737373);
                            child.material.transparent = true;
                        }
                    });
                    that.revertedObject = object;

                    that.addFromList();
                });
            });

        };

        this.load3dObj();

        this.toxicParamsGenerator.addGuiControls(gui, this.toxicObjects);

        var elementOnMouseDown = -1000;

        function setMousePoistion(event, mouse) {

            event.preventDefault();

            var viewportOffset = animate.containerEle[0].getBoundingClientRect(); //FIXME: calculate only on resize
            var top = viewportOffset.top;
            var left = viewportOffset.left;

            var clientX,
                clientY;

            if (event.originalEvent && event.originalEvent.changedTouches) {
                clientX = event.originalEvent.changedTouches[0].clientX;
                clientY = event.originalEvent.changedTouches[0].clientY;
            }

            if (!isNaN(event.clientX)) {
                clientX = event.clientX;
                clientY = event.clientY;
            }

            var cX = clientX - left,
                cY = clientY - top;

            mouse.x = (cX / viewportOffset.width) * 2 - 1;
            mouse.y = -(cY / viewportOffset.height) * 2 + 1;
            mouse.cx = cX;
            mouse.cy = cY;
        }


        this.onDocumentMouseMove = function (event) {
            // these are relative to the viewport
            setMousePoistion(event, mouse);
        };

        this.onDocumentTouchEnd = function (event) {
            listiner('startSpin');
            setMousePoistion(event, mouse);

            if (elementOnMouseDown === that.selectedElementIndex) {
                that.clickElement(that.selectedElementIndex);
            }
            elementOnMouseDown = -1000;

        };

        this.onDocumentTouchStart = function (event) {
            listiner('stopSpin');
            setMousePoistion(event, mouse);

            if (that.selectedElementIndex) {
                elementOnMouseDown = that.selectedElementIndex;
            }
        };

        this.onDocumentMouseDown = function () {
            listiner('stopSpin');
            if (that.selectedElementIndex) {
                elementOnMouseDown = that.selectedElementIndex;
            }
        };
        this.onDocumentMouseUp = function () {
            listiner('startSpin');
            if (elementOnMouseDown === that.selectedElementIndex) {
                that.clickElement(that.selectedElementIndex);
            }
            elementOnMouseDown = -1000;
        };

        this.hoverElement = function (ele) {
            if (!ele) {
                elementOnMouseDown = -1000;
                return;
            }
            if (that.selectedElementIndex !== ele.indexId) {
                that.selectedElement = ele;
                that.selectedElementIndex = ele.indexId;
            }
        };

        this.clickElement = function (currentElement) {

            listiner('addCommentsData', currentElement);
            var tokens = window.location.hash.split('/');
            tokens[2] = that.selectedElement.revid;
            window.location.hash = tokens.join('/');
            this.startZoomAnimation(function () {
                listiner('switchScreenToComments', currentElement);
            });
        };

        function getCenterPoint(mesh) {
            var middle = new THREE.Vector3();
            var geometry = mesh.geometry;

            geometry.computeBoundingBox();

            middle.x = (geometry.boundingBox.max.x + geometry.boundingBox.min.x) / 2;
            middle.y = (geometry.boundingBox.max.y + geometry.boundingBox.min.y) / 2;
            middle.z = (geometry.boundingBox.max.z + geometry.boundingBox.min.z) / 2;

            mesh.localToWorld(middle);
            return middle;
        }

        this.startZoomAnimation = function (cb) {
            listiner('stopSpin');
            this.inZoomAnimation = true;
            this.animate.controls.enabled = false;
            that.toxicObjects.updateMatrixWorld();
            var vector = getCenterPoint(that.selectedElement);
            //vector.setFromMatrixPosition( that.selectedElement.matrixWorld );

            var moveTo = vector.clone();

            var box = new THREE.Box3().setFromObject(that.selectedElement);


            var distanceToObject = this.animate.camera.position.clone().distanceTo(vector),
                alpha = box.size().x / distanceToObject;

            moveTo.lerp(this.animate.camera.position.clone(), alpha);


            //var position = that.selectedElement.position;
            //this.animate.controls.target.set(position.x,position.y, position.z);

            TWEEN.removeAll();


            new TWEEN.Tween(this.animate.controls.target).to({
                x: vector.x,
                y: vector.y,
                z: vector.z
            }, 800).easing(TWEEN.Easing.Exponential.Out).onComplete(cb).start();

            new TWEEN.Tween(this.animate.camera.position).to({
                x: moveTo.x,
                y: moveTo.y,
                z: moveTo.z
            }, 800).easing(TWEEN.Easing.Exponential.Out).start();

        };

        this.renderUpdates = function () {

            var that = this;

            this.toxicObjects.children.forEach(function (obj) {
                //obj.rotation.x += obj.rotationThreshold;
                //obj.rotation.y += obj.rotationThreshold;
                obj.rotation[obj.ramdomRotationAxis] += obj.rotationThreshold;
            });


            raycaster.setFromCamera(mouse, that.animate.camera);
            var intersects = raycaster.intersectObjects(that.toxicObjects.children, true);
            if (intersects.length > 0) {
                if (INTERSECTED != intersects[0].object) {
                    INTERSECTED = intersects[0].object;
                    that.hoverElement(INTERSECTED, mouse);
                }
            } else {
                that.hoverElement(false, mouse);
                INTERSECTED = null;
            }

        };

        $(animate.containerEle).on('mousemove', that.onDocumentMouseMove);
        $(animate.containerEle)[0].addEventListener('mousedown', that.onDocumentMouseDown, true);
        $(animate.containerEle).on('mouseup', that.onDocumentMouseUp);
        $(animate.containerEle).on('touchend', that.onDocumentTouchEnd);
        $(animate.containerEle).on('touchstart', that.onDocumentTouchStart);

    }

    return toxicParticle;

});
