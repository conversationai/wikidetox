<template>
  <div id="container">
  </div>
</template>

<script>
import {
  mapState,
  mapGetters
} from 'vuex'
import * as THREE from 'three'
import * as OrbitControls from 'three-orbitcontrols'

import {
  Particles
} from './particleSystem/Particles.js'

export default {
  name: 'ParticleSystem',
  data () {
    return {
      width: 0,
      height: 0,
      view: null,
      renderer: null,
      scene: null,
      mouse: null,
      camera: null,
      resolution: null,
      particleSystem: null,
      particles: null,
      pointclouds: null,
      INTERSECTED: null,
      deletionComplete: false
    }
  },
  computed: {
    ...mapState({
      sortby: state => state.sort,
      datas: state => state.datas,
      month: state => state.SELECTED_MONTH
      // toxLength: state => state.toxicLength,
      // detoxedLength: state => state.detoxedLength
    }),
    ...mapGetters({
      dataTimeRange: 'getDataTimeRange'
    })
  },
  watch: {
    month (newVal, oldVal) {
      if (this.datas.length > 0) {
        console.log('not first paint')
        this.particleSystem.particles.exit = true
        // this.deletionComplete = true
      }
    },
    datas (newVal, oldVal) {
      if (oldVal.length !== 0) {
        this.scene.remove(this.particles)
      }
      this.addParticles()
    }
  },
  mounted () {
    window.addEventListener('resize', this.resize, false)
    window.addEventListener('mousemove', this.onMouseMove, false)
    this.init()
  },
  beforeDestroy () {
    window.removeEventListener('resize', this.resize)
    window.removeEventListener('mousemove', this.onMouseMove)
  },
  methods: {
    init () {
      this.renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: true
      })
      this.view = document.getElementById('container')
      this.renderer.setSize(this.view.clientWidth, this.view.clientHeight)
      this.view.appendChild(this.renderer.domElement)

      this.camera = new THREE.PerspectiveCamera(45, this.view.clientWidth / this.view.clientHeight, 1, 10000)
      this.camera.position.z = 100
      this.scene = new THREE.Scene()
      this.scene.add(new THREE.AmbientLight(0xffffff))
      this.controls = new OrbitControls(this.camera, this.view)

      // Helpers
      // var axesHelper = new THREE.AxesHelper(5)
      // this.scene.add(axesHelper)

      // Initialize RAYCASTER
      this.raycaster = new THREE.Raycaster()
      this.mouse = new THREE.Vector2()
      this.animate()
    },
    resize () {
      this.camera.aspect = this.view.clientWidth / this.view.clientHeight
      this.camera.updateProjectionMatrix()
      this.renderer.setSize(this.view.clientWidth, this.view.clientHeight)
    },
    animate () {
      requestAnimationFrame(this.animate)
      this.render()
    },
    render () {
      this.camera.updateProjectionMatrix()
      this.controls.update()
      this.raycaster.setFromCamera(this.mouse, this.camera)

      // raycaster events
      let intersects = this.raycaster.intersectObjects(this.scene.children, true)

      if (intersects.length > 0) {
        if (this.INTERSECTED !== intersects[0].index) {
          this.INTERSECTED = intersects[ 0 ].index
          // console.log(this.INTERSECTED)
          console.log(this.datas[this.INTERSECTED])
        }
      } else {
        this.INTERSECTED = null
      }

      this.renderer.render(this.scene, this.camera)
    },
    addParticles () {
      this.particleSystem = new Particles({
        datas: this.datas
      })
      this.particles = this.particleSystem.particles
      this.attributes = this.particles.geometry.attributes
      this.scene.add(this.particles)
    },
    onMouseMove (event) {
      this.mouse.x = (event.clientX / this.view.clientWidth) * 2 - 1
      this.mouse.y = -(event.clientY / this.view.clientHeight) * 2 + 1
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped lang="scss">
  #container {
    position: fixed;
    top: 0;
    left: 0;
    z-index: 1;
    width: 100vw;
    height: calc(100vh - 76px);
  }
</style>
