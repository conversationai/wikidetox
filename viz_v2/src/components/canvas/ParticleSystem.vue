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
import anime from 'animejs'

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
      particleSystem: null,
      particles: null,
      pointclouds: null,
      INTERSECTED: null,
      deletionComplete: false
    }
  },
  computed: {
    ...mapState({
      sortby: state => state.sortby,
      filterby: state => state.filterby,
      datas: state => state.datas,
      month: state => state.SELECTED_MONTH
      // toxLength: state => state.toxicLength,
      // detoxedLength: state => state.detoxedLength
    }),
    ...mapGetters({
      canvasState: 'getCanvas',
      dataTimeRange: 'getDataTimeRange',
      talkPage: 'getTalkpage',
      userPage: 'getUserpage'
    })
  },
  watch: {
    sortby (newVal, oldVal) {
      if (newVal === 'all') {
        this.addParticles(this.datas)
        this.particlesZoomIn()
      } else {
        this.particlesZoomout()
      }
    },
    filterby (newVal, oldVal) {
      if (newVal === null) {
        this.particlesZoomout()
      } else {
        this.addFilteredParticles()
      }
    },
    month (newVal, oldVal) {
      if (this.datas.length > 0) {
        console.log('not first paint')
        this.particleSystem.particles.exit = true
      }
    },
    datas (newVal, oldVal) {
      if (this.canvasState === 'particles') {
        if (this.sortby === 'all') {
          this.addParticles(newVal)
        } else {
          this.addFilteredParticles()
        }
      }
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
    addParticles (datas) {
      if (this.particles !== null) {
        this.scene.remove(this.particles)
      }
      this.particleSystem = new Particles({
        datas: datas
      })
      this.particles = this.particleSystem.particles
      this.attributes = this.particles.geometry.attributes
      this.scene.add(this.particles)
      console.log(this.particles)
    },
    addFilteredParticles () {
      let datas
      if (this.sortby === 'type') {
        datas = this.filterby.startsWith('User') ? this.userPage : this.talkPage
      } else if (this.sortby === 'trend') {
        datas = this.datas.filter(d => d['type'] !== 'DELETION')
        datas = datas.filter(d => d['Category'] === this.filterby || d['Sub Category'] === this.filterby)
      } else if (this.sortby === 'model') {
        datas = this.datas.filter(d => Number(d[this.filterby]) >= 0.8 && d['type'] !== 'DELETION')
      } else {
        console.log('ERR: filter type not defined')
      }
      this.addParticles(datas)
    },
    onMouseMove (event) {
      this.mouse.x = (event.clientX / this.view.clientWidth) * 2 - 1
      this.mouse.y = -(event.clientY / this.view.clientHeight) * 2 + 1
    },
    particlesZoomIn () {
      this.particles.visible = true
      console.log(this.particles)
      anime({
        targets: this.particles.scale,
        x: 1,
        y: 1,
        z: 1,
        loop: false,
        easing: 'linear',
        duration: 200
      })
    },
    particlesZoomout () {
      anime({
        targets: this.particles.scale,
        x: 0.001,
        y: 0.001,
        z: 0.001,
        loop: false,
        easing: 'linear',
        duration: 200,
        complete: () => {
          this.particles.visible = false
        }
      })
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped lang="scss">
  #container {
    position: fixed;
    top: 0;
    left: 6vw;
    z-index: 1;
    width: 94vw;
    height: calc(100vh - 106px);
  }
</style>
