<template>
  <div id="container"></div>
</template>

<script>
import {
  mapState,
  mapGetters
} from 'vuex'
import * as THREE from 'three'
import * as OrbitControls from 'three-orbitcontrols'
import SphereMixin from './sphereFunctions.js'
import { Particle } from './Particle.js'

export default {
  name: 'MainCanvas',
  mixins: [SphereMixin],
  data () {
    return {
      width: 0,
      height: 0,
      camera: null,
      scene: null,
      view: null,
      renderer: null,
      controls: null,
      raycaster: null,
      mouse: null,
      particleGroup: null,
      animationGroup: null,
      collidedMesh: null,
      clock: null,
      particles: []
    }
  },
  computed: {
    ...mapState({
      sortby: state => state.sort,
      datas: state => state.datas
    }),
    ...mapGetters({
      dataTimeRange: 'getDataTimeRange'
    }),
    spritPNG () {
      return require('../../assets/glow.png')
    }
  },
  watch: {
    datas (newVal, oldVal) {
      console.log('datas changed')
      this.addToxParticles()
    }
  },
  mounted () {
    window.addEventListener('resize', this.resize, false)
    window.addEventListener('mousemove', this.onMouseMove, false)
    this.init()
    if (this.datas) {
      this.addToxParticles()
    }
  },
  beforeDestroy () {
    window.removeEventListener('resize', this.resize)
    window.removeEventListener('mousemove', this.onMouseMove)
  },
  methods: {
    init () {
      this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
      this.view = document.getElementById('container')
      this.renderer.setSize(this.view.clientWidth, this.view.clientHeight)
      this.view.appendChild(this.renderer.domElement)

      this.camera = new THREE.PerspectiveCamera(45, this.view.clientWidth / this.view.clientHeight, 1, 10000)
      this.camera.position.z = 100
      this.scene = new THREE.Scene()
      this.scene.add(new THREE.AmbientLight(0x333333))
      this.controls = new OrbitControls(this.camera, this.view)

      this.clock = new THREE.Clock()

      // Initialize group animation
      this.animationGroup = new THREE.AnimationObjectGroup()
      this.particleGroup = new THREE.Object3D()

      // // create clip
      // const fadeinClip = new THREE.AnimationClip('fadeIn', 3, [ ])

      // // apply the animation group to the mixer as the root object
      // const mixer = new THREE.AnimationMixer(this.particleGroup)
      // const fadeinAction = mixer.clipAction(fadeinClip)
      // fadeinAction.play()

      // Helpers
      const stats = new Stats()
      document.body.appendChild(stats.dom)
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
    render () {
      this.camera.updateProjectionMatrix()
      this.controls.update()
      this.raycaster.setFromCamera(this.mouse, this.camera)

      // SPHERE ROTATION
      // this.particleGroup.rotation.y += 0.001

      // HOVER EVENT
      let intersects = this.raycaster.intersectObjects(this.particleGroup.children)
      if (intersects.length > 0) {
        if (intersects[0].object !== this.collidedMesh) {
          if (this.collidedMesh !== null) {
            this.collidedMesh.material.color.setHex(this.collidedMesh.currentHex)
            this.collidedMesh = null
          }
          this.collidedMesh = intersects[0].object
          this.collidedMesh.currentHex = this.collidedMesh.material.color.getHex()
          intersects[0].object.material.color.setHex(0xFFF5B0)
        }
      } else {
        if (this.collidedMesh !== null) {
          this.collidedMesh.material.color.setHex(this.collidedMesh.currentHex)
          this.collidedMesh = null
        }
      }

      this.renderer.render(this.scene, this.camera)
    },
    animate () {
      requestAnimationFrame(this.animate)
      this.render()
    },
    onMouseMove (event) {
      this.mouse.x = (event.clientX / window.innerWidth) * 2 - 1
      this.mouse.y = -(event.clientY / window.innerHeight) * 2 + 1
    },
    addToxParticles () {
      const geometry = new THREE.SphereGeometry(1, 12, 6)
      this.datas.forEach((d, i) => {
        const newPos = this.fibonacciSphere(i)
        this.particles.push(new Particle({
          group: this.particleGroup,
          animationGroup: this.animationGroup,
          x: newPos.x,
          y: newPos.y,
          z: newPos.z,
          delay: i,
          color: d.type === 'DELETION' ? 0xffffff : 0xE63C5B,
          size: d.type === 'DELETION' ? 0.3 : (Number(d.Toxicity) - 0.75) * 7,
          commentID: d.id,
          geometry: geometry
        }))
      })
      this.scene.add(this.particleGroup)
    },
    random (floor, ceiling) {
      return (Math.random() * ceiling | 0) + floor
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
