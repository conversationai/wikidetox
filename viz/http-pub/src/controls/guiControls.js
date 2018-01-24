/*jslint vars: true, plusplus: true, devel: true, nomen: true, indent: 4, maxerr: 50 */
/*global require, define, THREE, brackets: true , dat*/

define(['../../libs/dat.gui'], function () {

    dat.GUI.prototype.removeFolder = function (name) {
        var folder = this.__folders[name];
        if (!folder) {
            return;
        }
        folder.close();
        this.__ul.removeChild(folder.domElement.parentNode);
        delete this.__folders[name];
        this.onResize();
    };

    dat.GUI.prototype.saveCurrentValues = function () {

        var props = {};
        for (var i in this.__folders) {

            for (var j in this.__folders[i].__folders) {
                if (!props[i]) {
                    props[i] = {};
                }
                if (!props[i][j]) {
                    props[i][j] = {};
                }
                this.__folders[i].__folders[j].__controllers.forEach(function (d) {
                    props[i][j][d.property] = d.__input ? d.__input.value : d.getValue();
                })
            }

            this.__folders[i].__controllers.forEach(function (d) {
                if (!props[i]) {
                    props[i] = {};
                }
                props[i][d.property] = d.__input ? d.__input.value : d.getValue();
            })
        }
        console.log(JSON.stringify(props));
        window.prompt("Copy to clipboard: Ctrl+C, Enter", JSON.stringify(props));
    };

    return function () {
        this.gui = new dat.GUI({
            autoPlace: false
        });

        this.gui.close();

        return this.gui;
    }

});
