<template>
  <div id="container" ref="container"
      :class="{'expanded': commentClicked}">
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
      view: null,
      renderer: null,
      scene: null,
      mouse: null,
      camera: null,
      controls: null,
      particleSystem: null,
      particles: null,
      preZoomPos: null,
      zDist: 60,
      fov: 0,
      menuWidth: 0,
      radiusScale: 18,
      pointclouds: null,
      INTERSECTED: null, // Changes with raycaster every paint
      lookAtPos: [0, 0, 0],
      filteredData: [],
      viewedData: [],
      lastCommentIndex: null
    }
  },
  computed: {
    ...mapState({
      sortby: state => state.sortby,
      filterby: state => state.filterby,
      datas: state => state.datas,
      commentClicked: state => state.commentClicked, // boolean
      selectedDate: state => state.selectedDate,
      detoxedIndex: state => state.detoxedIndex
    }),
    ...mapGetters({
      talkPage: 'getTalkpage',
      userPage: 'getUserpage',
      dataTime: 'getDataTimeRange'
    })
  },
  watch: {
    filterby (newVal, oldVal) {
      if (newVal === null) {
        this.addParticles(this.datas)
      } else {
        this.addFilteredParticles()
      }
    },
    dataTime () {
      if (this.datas.length > 0) {
        this.particleSystem.animateExit()
      }
    },
    datas (newVal, oldVal) {
      TWEEN.removeAll()
      this.addParticles(newVal)
    },
    selectedDate (newVal, oldVal) {
      if (newVal !== null) {
        this.filteredData.forEach((d, i) => {
          const dataDate = d.timestamp.value.substr(0, 10)
          if (dataDate !== newVal) {
            this.growOut(i)
          } else {
            this.growIn(i)
          }
        })
      } else {
        this.$store.commit('CHANGE_COMMENT', null)
        this.filteredData.forEach((d, i) => {
          this.growIn(i)
        })
      }
    },
    commentClicked (newVal, oldVal) {
      this.resize()

      if (newVal) { // if clicked = true
        const clickedIndex = this.INTERSECTED
        this.zoomAnimation(clickedIndex, true, true) // zoom in
        this.controls.enabled = false
      } else {
        this.zoomAnimation(this.lastCommentIndex, false, false) // zoom out
        this.controls.enabled = true
      }
    },
    detoxedIndex (newVal, oldVal) {
      console.log(newVal)
      this.detoxParticleColor(newVal)
    }
  },
  mounted () {
    window.addEventListener('resize', this.resize)
    window.addEventListener('mousemove', this.onMouseMove, false)
    this.init()

    // When "previous" / "next" is clicked on fullscreen comment
    this.$root.$on('next', d => {
      this.hoverAnimation(this.INTERSECTED, false) // hover leave from last comment

      if (this.INTERSECTED === 0 && d < 0) {
        this.INTERSECTED = this.filteredData.length - 1
      } else if (this.INTERSECTED === this.filteredData.length - 1 && d > 0) {
        this.INTERSECTED = 0
      } else {
        this.INTERSECTED = this.INTERSECTED + d
      }
      // console.log(this.INTERSECTED)
      this.hoverAnimation(this.INTERSECTED, true) // hover leave
      this.zoomAnimation(this.INTERSECTED, true, false)
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
      this.getResizedValue()

      this.renderer.setSize(this.width, this.height)
      this.view.appendChild(this.renderer.domElement)
      this.camera = new THREE.PerspectiveCamera(this.fov, this.width / this.height, 1, 1000)
      this.camera.position.set(0, 0, this.zDist)

      this.scene = new THREE.Scene()
      this.scene.add(new THREE.AmbientLight(0xffffff))
      this.controls = new OrbitControls(this.camera, this.view)

      this.controls.minDistance = 40
      this.controls.maxDistance = 70

      this.controls.enablePan = false
      this.controls.enableRotate = true
      this.controls.enableZoom = true
      this.controls.rotateSpeed = 0.5
      this.controls.zoomSpeed = 0.5

      // Initialize RAYCASTER
      this.raycaster = new THREE.Raycaster()
      this.mouse = new THREE.Vector2()

      this.animate()
    },
    resize () {
      this.getResizedValue()

      this.camera.fov = this.fov
      this.camera.aspect = this.width / this.height
      this.camera.updateProjectionMatrix()
      this.renderer.setSize(this.width, this.height)
    },
    getResizedValue () {
      const w = window.innerWidth
      const breakPoint = 768
      if (w <= breakPoint) {
        // mobile / tablet
        this.menuWidth = 0
        this.height = this.$refs.container.clientHeight - 64
        this.fov = 2 * Math.tan((this.radiusScale / 0.6) / this.zDist) * (180 / Math.PI)
      } else {
        // desktop
        this.menuWidth = 262
        this.height = this.$refs.container.clientHeight
        this.fov = 2 * Math.atan((this.radiusScale / 0.74) / this.zDist) * (180 / Math.PI)
      }

      if (this.commentClicked) {
        this.width = w
      } else {
        this.width = w - this.menuWidth
      }
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
            this.$store.commit('CHANGE_COMMENT', null)
            this.hoverAnimation(this.INTERSECTED, false) // hover out of previous

            if (intersects[0].index !== null) {
              this.INTERSECTED = intersects[0].index
              this.hoverAnimation(this.INTERSECTED, true) // if mouse in = true
            }
          }
        } else {
          // If no intersection
          if (this.INTERSECTED !== null) {
            this.particleSystem.spin = true
            // clear previous intersection
            this.$store.commit('CHANGE_COMMENT', null)
            this.hoverAnimation(this.INTERSECTED, false) // if mouse in = true
            this.INTERSECTED = null
          }
        }
      }
      this.renderer.render(this.scene, this.camera)
    },
    addParticles (datas) {
      this.controls.reset()
      console.log(datas)
      this.filteredData = datas
      if (this.particles !== null) {
        this.scene.remove(this.particles)
      }
      this.particleSystem = new Particles({
        datas: datas,
        scale: this.radiusScale
      })

      this.particles = this.particleSystem.particles
      this.attributes = this.particles.geometry.attributes
      console.log(this.particles)
      this.scene.add(this.particles)
    },
    addFilteredParticles () {
      let datas
      if (this.sortby === 'type') {
        datas = this.filterby.startsWith('User') ? this.userPage : this.talkPage
      } else if (this.sortby === 'trend') {
        datas = this.datas.filter(d => d['type'] !== 'DELETION')
        const categories = ['category1', 'sub_category1', 'category2', 'sub_category2', 'category3', 'sub_category3']

        datas = this.datas.filter(d => {
          for (const c of categories) {
            if (d[c] === this.filterby) { return true }
          }
          return false
        })
      } else if (this.sortby === 'model') {
        datas = this.datas.filter(d => Number(d[this.filterby]) >= 0.8 && d['type'] !== 'DELETION')
      } else {
        console.log('ERR: filter type not defined')
      }
      this.addParticles(datas)
    },
    onMouseMove (event) {
      event.preventDefault()
      let offsetX = window.innerWidth <= 768 ? 0 : 262
      this.mouse.x = ((event.clientX - offsetX) / this.view.clientWidth) * 2 - 1
      this.mouse.y = -((event.clientY) / this.view.clientHeight) * 2 + 1
    },
    growOut (i) { // todo: move to particle class
      new TWEEN.Tween({ scale: this.attributes.scale.array[ i ] })
        .to({ scale: 1 }, 200)
        .easing(TWEEN.Easing.Linear.None)
        .onUpdate((obj) => {
          this.attributes.scale.array[ i ] = obj.scale
          this.attributes.scale.needsUpdate = true
        })
        .start()
    },
    growIn (i) { // todo: move to particle class
      new TWEEN.Tween({ scale: 1 })
        .to({ scale: this.attributes.finalSizes.array[ i ] }, 200)
        .easing(TWEEN.Easing.Linear.None)
        .onUpdate((obj) => {
          this.attributes.scale.array[ i ] = obj.scale
          this.attributes.scale.needsUpdate = true
        })
        .start()
    },
    commitHoveredComment (isMouseIn, commentIndex, finalSize) {
      if (isMouseIn) {
        if (commentIndex === this.INTERSECTED) {
          const position = this.getScreenPosition(commentIndex)
          this.$store.commit('CHANGE_COMMENT', {
            comment: this.filteredData[commentIndex],
            index: [commentIndex],
            pos: position,
            size: finalSize
          })
        }
      } else {
        // hover out
        this.lastCommentIndex = commentIndex
      }
    },
    hoverAnimation (commentIndex, isMouseIn) { // animation on particle hover
      let finalSize
      if (isMouseIn) {
        // Mouse in
        finalSize = 46
      } else {
        // Mouse out
        finalSize = this.attributes.finalSizes.array[ commentIndex ] // final scale = finalsizes
      }
      this.animateParticleSize(isMouseIn, commentIndex, finalSize)
    },
    zoomAnimation (commentIndex, ifZoomIn, firstZoom) { // Zoom animation on particle click
      let camPos, controlTarget
      const vec = this.getVectorPos(commentIndex)

      this.controls.minDistance = 0
      this.controls.update()
      const altitude = 10
      const coeff = 1 + altitude / this.particleSystem.radius

      if (ifZoomIn) {
        if (firstZoom) { this.preZoomPos = Object.assign({}, this.camera.position) }

        this.animateParticleColor(commentIndex)
        camPos = {
          x: vec.x * coeff,
          y: vec.y * coeff,
          z: vec.z * coeff
        }
        controlTarget = vec
      } else {
        camPos = this.preZoomPos
        controlTarget = { x: 0, y: 0, z: 0 }
      }

      this.animateControlTarget(ifZoomIn, controlTarget)
      this.animateCameraPos(camPos)
    },
    animateParticleSize (isMouseIn, commentIndex, finalSize) { // todo: move to particle class
      const baseSize = this.attributes.scale.array[ commentIndex ]
      new TWEEN.Tween({ scale: baseSize })
        .to({ scale: finalSize }, 200)
        .easing(TWEEN.Easing.Linear.None)
        .onUpdate((obj) => {
          this.attributes.scale.array[ commentIndex ] = obj.scale
          this.attributes.scale.needsUpdate = true
        })
        .onComplete(() => {
          // particle expanded -> show text
          // console.log(`commiting hovered comment ${commentIndex}`)
          this.commitHoveredComment(isMouseIn, commentIndex, finalSize)
        })
        .start()
    },
    animateParticleColor (commentIndex) { // todo: move to particle class
      // console.log(`animating particle color ${commentIndex}`)
      const baseRColor = this.attributes.vertexColor.array[ commentIndex * 4 ]
      new TWEEN.Tween({ red: baseRColor })
        .to({ red: 1 }, 100)
        .easing(TWEEN.Easing.Linear.None)
        .onUpdate((obj) => {
          this.attributes.vertexColor.array[ commentIndex * 4 ] = obj.red
          this.attributes.vertexColor.needsUpdate = true
        })
        .start()
    },
    detoxParticleColor (commentIndex) { // todo: move to particle class
      // console.log(`animating particle color ${commentIndex}`)
      const colorArray = this.attributes.vertexColor.array
      new TWEEN.Tween(
        {
          r: colorArray[commentIndex * 4],
          g: colorArray[commentIndex * 4 + 1],
          b: colorArray[commentIndex * 4 + 2]
        })
        .to({ r: 0.988, g: 0.91, b: 0.92 }, 100)
        .easing(TWEEN.Easing.Linear.None)
        .onUpdate((obj) => {
          colorArray[ commentIndex * 4 ] = obj.r
          colorArray[ commentIndex * 4 + 1 ] = obj.g
          colorArray[ commentIndex * 4 + 2 ] = obj.b
          this.attributes.vertexColor.needsUpdate = true
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
            this.controls.minDistance = 40
            this.controls.update()
          }
        })
        .start()
    },
    animateCameraPos (toPos) {
      // console.log(toPos)
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
    position: absolute;
    top: 0;
    right: 0;
    width:  100%;
    height: 100vh;
    z-index: 1;

    @include tablet {
      top: 64px;
    }
  }
</style>
