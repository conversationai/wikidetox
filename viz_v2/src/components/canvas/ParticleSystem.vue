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
import TWEEN from '@tweenjs/tween.js'
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
      lookAtPos: [0, 0, 0],
      filteredData: [],
      lastCommentIndex: null
    }
  },
  computed: {
    ...mapState({
      sortby: state => state.sortby,
      filterby: state => state.filterby,
      datas: state => state.datas,
      month: state => state.SELECTED_MONTH,
      commentClicked: state => state.commentClicked, // boolean
      selectedDate: state => state.selectedDate
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
      TWEEN.removeAll()
      if (this.canvasState === 'particles') {
        if (this.sortby === 'all') {
          this.addParticles(newVal)
        } else {
          this.addFilteredParticles()
        }
      }
    },
    selectedDate (newVal, oldVal) {
      // date hovered
      if (newVal !== null) {
        this.filteredData.forEach((d, i) => {
          const dataDate = d.timestamp.toISOString().substr(0, 10)
          if (dataDate !== newVal) {
            this.growOut(i)
          } else {
            this.growIn(i)
          }
        })
      } else {
        this.filteredData.forEach((d, i) => {
          this.growIn(i)
        })
      }
    },
    commentClicked (newVal, oldVal) {
      if (newVal) { // if clicked = true
        this.attributes.vertexColor.array[ this.INTERSECTED * 4 ] = 1
        this.attributes.vertexColor.needsUpdate = true
        this.zoomAnimation(this.INTERSECTED, true)
      } else {
        this.zoomAnimation(this.lastCommentIndex, false)
      }
    }
  },
  mounted () {
    window.addEventListener('resize', this.resize)
    window.addEventListener('mousemove', this.onMouseMove, false)
    this.init()

    // When "previous" / "next" is clicked on fullscreen comment
    this.$root.$on('next', d => {
      this.hoverAnimation(this.INTERSECTED, false)
      this.INTERSECTED = this.INTERSECTED + d
      this.hoverAnimation(this.INTERSECTED, true)
      this.zoomAnimation(this.INTERSECTED, true)
    })
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
      this.width = window.innerWidth
      this.height = window.innerHeight - 76

      this.renderer.setSize(this.width, this.height)
      this.view.appendChild(this.renderer.domElement)

      this.camera = new THREE.PerspectiveCamera(45, this.width / this.height, 1, 10000)
      this.camera.position.set(0, 0, 100)

      this.scene = new THREE.Scene()
      this.scene.add(new THREE.AmbientLight(0xffffff))
      this.controls = new OrbitControls(this.camera, this.view)

      // this.controls.minDistance = 70
      // this.controls.maxDistance = 90

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
      this.width = window.innerWidth
      if (this.commentClicked) {
        this.height = window.innerHeight
      } else {
        this.height = this.view.clientHeight - 76
      }

      this.camera.aspect = this.width / this.height
      this.camera.updateProjectionMatrix()
      this.renderer.setSize(this.width, this.height)
    },
    animate () {
      requestAnimationFrame(this.animate)
      this.render()
    },
    render () {
      this.camera.updateProjectionMatrix()
      this.controls.update()
      this.raycaster.setFromCamera(this.mouse, this.camera)
      this.raycaster.far = 90

      TWEEN.update()

      // raycaster events HOVER TRIGGER

      let intersects = this.raycaster.intersectObjects(this.scene.children, true)

      if (this.particles && this.particleSystem.finishedLoading && !this.commentClicked) {
        // If particles exist and finished loading animation
        this.particles.updateMatrixWorld()

        if (intersects.length > 0) {
          // If has intersection
          this.particleSystem.spin = false
          // clear previous hover and add new hover animation
          if (this.INTERSECTED !== intersects[0].index) {
            this.hoverAnimation(this.INTERSECTED, false) // hover out of previous
            this.INTERSECTED = intersects[0].index
            this.hoverAnimation(this.INTERSECTED, true) // if mouse in = true
          }
        } else {
          // If no intersection
          if (this.INTERSECTED !== null) {
            this.particleSystem.spin = true
            // clear previous intersection
            this.hoverAnimation(this.INTERSECTED, false) // if mouse in = true
            this.INTERSECTED = null
          }
        }
      }

      this.renderer.render(this.scene, this.camera)
    },
    addParticles (datas) {
      this.controls.reset()

      this.filteredData = datas
      if (this.particles !== null) {
        this.scene.remove(this.particles)
      }
      this.particleSystem = new Particles({
        datas: datas
      })

      this.particles = this.particleSystem.particles
      this.attributes = this.particles.geometry.attributes
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
    growOut (i) {
      new TWEEN.Tween({ scale: this.attributes.scale.array[ i ] })
        .to({ scale: 1 }, 200)
        .easing(TWEEN.Easing.Linear.None)
        .onUpdate((obj) => {
          this.attributes.scale.array[ i ] = obj.scale
          this.attributes.scale.needsUpdate = true
        })
        .start()
    },
    growIn (i) {
      new TWEEN.Tween({ scale: 1 })
        .to({ scale: this.attributes.finalSizes.array[ i ] }, 200)
        .easing(TWEEN.Easing.Linear.None)
        .onUpdate((obj) => {
          this.attributes.scale.array[ i ] = obj.scale
          this.attributes.scale.needsUpdate = true
        })
        .start()
    },
    commitSelectedComment (isMouseIn, commentIndex) {
      if (isMouseIn) {
        if (commentIndex === this.INTERSECTED) {
          const position = this.getScreenPosition(commentIndex)
          this.$store.commit('CHANGE_COMMENT', {
            comment: this.filteredData[commentIndex],
            pos: position
          })
        }
      } else {
        this.lastCommentIndex = commentIndex
        this.$store.commit('CHANGE_COMMENT', null)
      }
    },
    hoverAnimation (commentIndex, isMouseIn) { // animation on particle hover
      let finalSize, finalRColor
      if (isMouseIn) {
        // Mouse in
        finalSize = 60
        finalRColor = 1
      } else {
        // Mouse out
        finalSize = this.attributes.finalSizes.array[ commentIndex ] // final scale = finalsizes
        finalRColor = 0.9
      }
      this.animateParticleSizeColor(isMouseIn, commentIndex, finalSize, finalRColor)
    },
    zoomAnimation (commentIndex, ifZoomIn) { // Zoom animation on particle click
      this.resize()
      let camPos, controlTarget
      const vec = this.getVectorPos(commentIndex)

      if (ifZoomIn) {
        this.controls.minDistance = 0
        this.controls.update()
        const altitude = 14
        const coeff = 1 + altitude / this.particleSystem.radius
        camPos = {
          x: vec.x * coeff,
          y: vec.y * coeff,
          z: vec.z * coeff
        }
        controlTarget = vec
      } else {
        camPos = { x: 0, y: 0, z: 100 }
        controlTarget = { x: 0, y: 0, z: 0 }
      }

      this.animateControlTarget(ifZoomIn, controlTarget)
      this.animateCameraPos(camPos)
    },
    animateParticleSizeColor (isMouseIn, commentIndex, finalSize, finalRColor) {
      const baseSize = this.attributes.scale.array[ commentIndex ]
      const baseRColor = this.attributes.vertexColor.array[ commentIndex * 4 ]
      new TWEEN.Tween({ scale: baseSize, red: baseRColor })
        .to({ scale: finalSize, red: finalRColor }, 200)
        .easing(TWEEN.Easing.Linear.None)
        .onUpdate((obj) => {
          this.attributes.scale.array[ commentIndex ] = obj.scale
          this.attributes.scale.needsUpdate = true
          this.attributes.vertexColor.array[ commentIndex * 4 ] = obj.red
          this.attributes.vertexColor.needsUpdate = true
        })
        .onComplete(() => {
          // particle expanded -> show text
          this.commitSelectedComment(isMouseIn, commentIndex)
        })
        .start()
    },
    animateControlTarget (ifZoomIn, controlTarget) {
      const fromTarget = this.controls.target
      new TWEEN.Tween(fromTarget)
        .to(controlTarget)
        .easing(TWEEN.Easing.Linear.None)
        .onUpdate((vec) => {
          this.controls.target.copy(vec)
          this.controls.update()
        })
        .onComplete(() => {
          if (!ifZoomIn) {
            this.controls.minDistance = 70
            this.controls.update()
          }
        })
        .start()
    },
    animateCameraPos (toPos) {
      const fromPos = this.camera.position.clone()
      new TWEEN.Tween(fromPos)
        .to(toPos, 600)
        .easing(TWEEN.Easing.Linear.None)
        .onUpdate((vec) => {
          this.camera.position.copy(vec)
          this.controls.update()
        })
        .start()
    },
    getScreenPosition (i) {
      const vec = this.getVectorPos(i)
      vec.project(this.camera)
      return {
        x: Math.round((vec.x + 1) * this.width / 2),
        y: Math.round((-vec.y + 1) * this.height / 2)
      }
    },
    getVectorPos (i) {
      // Get world position of vector
      const posAttr = this.attributes.position
      const vector = {
        x: posAttr.array[ 3 * i ],
        y: posAttr.array[ 3 * i + 1 ],
        z: posAttr.array[ 3 * i + 2 ]
      }
      const localVector = new THREE.Vector3(vector.x, vector.y, vector.z)
      localVector.applyMatrix4(this.particles.matrixWorld) // Apply world position
      return localVector
    },
    particlesZoomIn () { // TODO: change to buffer animation
      this.particles.visible = true
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
    particlesZoomout () { // TODO: change to buffer animation
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
    left: 0;
    width: 100vw;
    height: calc(100vh - 76px);
    transition: .2s top;
    &.expanded {
      height: 100vh;
    }
  }
</style>
