import * as THREE from 'three'
import TWEEN from '@tweenjs/tween.js'
import { fibonacciSphere } from './sphereFunctions'

// Particle shader - takes scale (float) and color (vec4) variables

const particleVert = `
attribute float scale;
attribute float color;
attribute vec4 vertexColor;
varying vec4 vVertexColor;
void main() {
vec4 mvPosition = modelViewMatrix * vec4( position, 1.0 );
gl_PointSize = scale * ( 300.0 / - mvPosition.z );
  gl_Position = projectionMatrix * mvPosition;
  vVertexColor = vertexColor;
}
`

const particleFrag = `
precision highp float;
varying vec4 vVertexColor;
void main() {
  if ( length( gl_PointCoord - vec2( 0.5, 0.5 ) ) > 0.475 ) discard;
  gl_FragColor = vec4(vVertexColor);
}
`

export class Particles {
  constructor (config) {
    for (const [key, value] of Object.entries(config)) {
      this[`_${key}`] = value
    }
    this.spin = true
    this.exit = false
    this.radius = 0
    this.init()
  }
  init () {
    this.initGeometry()
    const particlesMaterial = new THREE.ShaderMaterial({
      // uniforms: {
      //   resolution: { value: new THREE.Vector2() }
      // },
      transparent: true,
      depthWrite: true,
      vertexShader: particleVert,
      fragmentShader: particleFrag
    })

    this.particles = new THREE.Points(this.particleGeometry, particlesMaterial)

    this.loadEntryAnimation()
    this.loadExitAnimation()
  }
  initGeometry () {
    this.particleGeometry = new THREE.BufferGeometry()
    const numPoints = this._datas.length
    let sphereScale = (numPoints - 200) / 220 * 4 + 18
    this.radius = sphereScale > 30 ? 30 : sphereScale
    let positions = new Float32Array(numPoints * 3)
    // let hoverPositions = new Float32Array(numPoints * 3)
    let colors = new Float32Array(numPoints * 4)
    let scale = new Float32Array(numPoints)
    let finalSizes = new Float32Array(numPoints)

    this._datas.forEach((d, i) => {
      const newPos = fibonacciSphere(numPoints, this.radius, i)
      positions[ 3 * i ] = newPos.x
      positions[3 * i + 1] = newPos.y
      positions[3 * i + 2] = newPos.z

      scale[i] = 0.001

      let color
      const sizeWeight = 3.6
      if (d.type === 'DELETION') {
        finalSizes[i] = sizeWeight
        color = [1, 1, 1]
      } else {
        finalSizes[i] = (Number(d.Toxicity) - 0.75) * sizeWeight * 20
        color = [0.9, 0.23, 0.36]
      }
      colors[ 4 * i ] = color[0]
      colors[ 4 * i + 1 ] = color[1]
      colors[ 4 * i + 2 ] = color[2]
      colors[ 4 * i + 3 ] = 1
    })
    this.particleGeometry.addAttribute('position', new THREE.BufferAttribute(positions, 3))
    // this.particleGeometry.addAttribute('hoverPositions', new THREE.BufferAttribute(hoverPositions, 3))
    this.particleGeometry.addAttribute('vertexColor', new THREE.BufferAttribute(colors, 4))
    this.particleGeometry.addAttribute('scale', new THREE.BufferAttribute(scale, 1))
    this.particleGeometry.addAttribute('finalSizes', new THREE.BufferAttribute(finalSizes, 1))
    this.particleGeometry.computeBoundingSphere()
  }
  loadEntryAnimation () {
    const _this = this
    _this.particles.onBeforeRender = () => {
      if (_this.exit) return
      const attr = this.particleGeometry.attributes
      // attr.vertexColor.needsUpdate = true

      // Loading animation
      const l = _this._datas.length

      for (let i = 0; i < l; i++) {
        // CALCULATING animation delay
        let weight
        if (l < 100) {
          // Larger wait time for smaller particle systems
          if (i > l - 10) {
            weight = l - 10
          } else {
            weight = i * 1.2
          }
        } else {
          if (i > l - 100) {
            weight = l - 100
          } else {
            weight = i
          }
        }
        if (attr.scale.array[i] < attr.finalSizes.array[i] - (1 - weight / l + 0.1)) {
          attr.scale.array[i] += (1 - weight / l + 0.1)
        } else {
          attr.scale.array[i] = attr.finalSizes.array[i]
        }
      }
      attr.scale.needsUpdate = true

      if (!_this.spin) return
      // _this.particles.rotation.y += 0.0002
    }
  }
  loadExitAnimation () {
    const _this = this
    // Immediately after first render
    _this.particles.onAfterRender = () => {
      if (!_this.exit) return
      const scale = this.particleGeometry.attributes.scale
      scale.needsUpdate = true

      // Exit animation
      const l = _this._datas.length

      for (let i = 0; i < l; i++) {
        let weight
        if (l < 100) {
          if (i > l - 10) {
            weight = l - 10
          } else {
            weight = i * 1.2
          }
        } else {
          if (i > l - 100) {
            weight = l - 100
          } else {
            weight = i
          }
        }
        if (scale.array[i] > (1 - weight / l + 0.1)) {
          scale.array[i] += -(1 - weight / l + 0.1)
        } else {
          scale.array[i] = 0
        }
      }
    }
  }
  zoomInAnimation (commentIndex) {
    this.spin = false
    console.log(commentIndex)

    const vec = this.getVectorPos(commentIndex)
    const moveTo = vec.clone()
    // const cam = this._camera.position.clone()
    // const distanceToObject = cam.distanceTo(vec)
    // const size = this.particleGeometry.attributes.finalSizes.array[commentIndex]
    // const alpha = size / distanceToObject
    // moveTo.lerp(cam, alpha)

    const altitude = 10
    const coeff = 1 + altitude / this.radius
    this._camera.position.set(vec.x * coeff, vec.y * coeff, vec.z * coeff)
    this._controls.target.set(vec.x, vec.y, vec.z)
    this._controls.update()

    // TWEEN.removeAll()
    // new TWEEN.Tween(this._camera.position).to({
    //   x: moveTo.x,
    //   y: moveTo.y,
    //   z: moveTo.z
    // }, 800).easing(TWEEN.Easing.Exponential.Out).start()

    // new TWEEN.Tween(this._camera.position).to({
    //   x: moveTo.x,
    //   y: moveTo.y,
    //   z: moveTo.z
    // }, 800).easing(TWEEN.Easing.Exponential.Out).start()
  }
  zoomOutAnimation () {
    this._camera.position.set(0, 0, 100)
    this._controls.target.set(0, 0, 0)

    this._controls.update()
    this.spin = true
  }
  getVectorPos (i) {
    const posAttr = this.particleGeometry.attributes.position
    const vector = {
      x: posAttr.array[ 3 * i ],
      y: posAttr.array[ 3 * i + 1 ],
      z: posAttr.array[ 3 * i + 2 ]
    }
    const threeVector = new THREE.Vector3(vector.x, vector.y, vector.z)
    return threeVector
  }
  animateExit () {
    this.exit = true
  }
}
