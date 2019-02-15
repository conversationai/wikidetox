<template>
  <div id="container"
      :class="{'expanded': commentClicked}"
      :style="{ zIndex: zindex }">
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
      zindex: 100,
      view: null,
      renderer: null,
      scene: null,
      mouse: null,
      camera: null,
      controls: null,
      particleSystem: null,
      particles: null,
      pointclouds: null,
      INTERSECTED: null, // Changes with raycaster every paint
      selectedIndex: null, // persistent index of hovered data
      lookAtPos: [0, 0, 0],
      filteredData: []
    }
  },
  computed: {
    ...mapState({
      sortby: state => state.sortby,
      filterby: state => state.filterby,
      datas: state => state.datas,
      month: state => state.SELECTED_MONTH,
      commentClicked: state => state.commentClicked, // boolean
      clickedIndex: state => state.clickedIndex // number
    }),
    ...mapGetters({
      canvasState: 'getCanvas',
      dataTimeRange: 'getDataTimeRange',
      talkPage: 'getTalkpage',
      userPage: 'getUserpage'
    })
  },
  watch: {
    canvasState (newVal, oldVal) {
      if (newVal === 'particles') {
        this.zindex = 100
      } else {
        this.zindex = 1
      }
    },
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
        this.particleSystem.animateExit()
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
    },
    clickedIndex (newVal, oldVal) { // idnex number of clicked comment
      if (newVal !== null) {
        this.particleSystem.zoomInAnimation(newVal)
        // Changes comment opacity
        this.attributes.vertexColor.array[ 4 * newVal + 3 ] = 0.6
        this.attributes.vertexColor.needsUpdate = true
      } else {
        this.particleSystem.zoomOutAnimation()
      }
    }
  },
  mounted () {
    window.addEventListener('resize', this.resize)
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
      this.camera.position.set(0, 0, 100)
      // this.camera.up = new THREE.Vector3(0, 0, 0)

      this.scene = new THREE.Scene()
      this.scene.add(new THREE.AmbientLight(0xffffff))
      this.controls = new OrbitControls(this.camera, this.view)
      // this.controls.minDistance = 70
      // this.controls.maxDistance = 100
      this.controls.enablePan = false
      this.controls.enableRotate = true
      this.controls.enableZoom = true
      this.controls.rotateSpeed = 0.5
      this.controls.zoomSpeed = 0.5

      // Helpers
      // var axesHelper = new THREE.AxesHelper(5)
      // this.scene.add(axesHelper)

      // Initialize RAYCASTER
      this.raycaster = new THREE.Raycaster()
      this.mouse = new THREE.Vector2()
      this.animate()
    },
    resize () {
      this.camera.aspect = this.view.clientWidth / window.innerHeight
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
      this.raycaster.far = 100
      // raycaster events
      let intersects = this.raycaster.intersectObjects(this.scene.children, true)

      if (intersects.length > 0 && !this.commentClicked) {
        if (this.INTERSECTED !== intersects[0].index) {
          this.INTERSECTED = intersects[0].index
          this.selectedIndex = intersects[0].index
          this.$store.commit('CHANGE_COMMENT', {
            index: this.INTERSECTED,
            comment: this.filteredData[this.INTERSECTED]
          })
        }
      } else {
        this.INTERSECTED = null
        this.$store.commit('CHANGE_COMMENT', null)
      }
      this.renderer.render(this.scene, this.camera)
    },
    addParticles (datas) {
      this.filteredData = datas
      if (this.particles !== null) {
        this.scene.remove(this.particles)
      }
      this.particleSystem = new Particles({
        datas: datas,
        controls: this.controls,
        camera: this.camera
      })

      this.particles = this.particleSystem.particles
      this.attributes = this.particles.geometry.attributes

      this.controls.reset()
      this.scene.add(this.particles)
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
      this.mouse.y = -(event.clientY / (this.view.clientHeight - 76)) * 2 + 1
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
    top: -76px;
    left: 0;
    width: 100vw;
    height: 100vh;
    transition: .2s top;
    &.expanded {
      top: 0;
    }
  }
</style>
