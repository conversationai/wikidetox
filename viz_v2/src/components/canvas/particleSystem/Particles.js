import * as THREE from 'three'
import { fibonacciSphere } from './sphereFunctions'

// Particle shader -- takes size and color variables

const particleVert = `
attribute float scale;
attribute float color;
attribute vec3 vertexColor;
varying vec3 vVertexColor;
void main() {
vec4 mvPosition = modelViewMatrix * vec4( position, 1.0 );
gl_PointSize = scale * ( 300.0 / - mvPosition.z );
  gl_Position = projectionMatrix * mvPosition;
  vVertexColor = vertexColor;
}
`

const particleFrag = `
precision highp float;
varying vec3 vVertexColor;
void main() {
  if ( length( gl_PointCoord - vec2( 0.5, 0.5 ) ) > 0.475 ) discard;
  gl_FragColor = vec4(vVertexColor, 0.9);
}
`

export class Particles {
  constructor (config) {
    // for (const [key, value] of Object.entries(config)) {
    //   this[key] = value
    // }
    this.entry = true
    this.exit = false
    this._allDatas = config.datas
    this._datas = config.datas
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
    this.particles.exit = false

    // Onbeforerender
    const l = this._datas.length
    this.particles.onBeforeRender = function () {
      if (this.exit) return
      const attr = this.geometry.attributes
      attr.scale.needsUpdate = true
      attr.position.needsUpdate = true
      // Loading animation
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
      // console.log(this)
      this.rotation.y += 0.0002
    }
    // onAfterRender -> immediately after first render
    this.particles.onAfterRender = function () {
      if (!this.exit) return
      const scale = this.geometry.attributes.scale
      scale.needsUpdate = true
      // Exit animation
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
  initGeometry () {
    this.particleGeometry = new THREE.BufferGeometry()
    const numPoints = this._datas.length
    let sphereScale = (numPoints - 200) / 220 * 4 + 18
    let radius = sphereScale > 33 ? 33 : sphereScale
    console.log(radius)

    let positions = new Float32Array(numPoints * 3)
    let colors = new Float32Array(numPoints * 3)
    let scale = new Float32Array(numPoints)
    let finalSizes = new Float32Array(numPoints)

    this._datas.forEach((d, i) => {
      const newPos = fibonacciSphere(numPoints, radius, i)
      positions[ 3 * i ] = newPos.x
      positions[3 * i + 1] = newPos.y
      positions[3 * i + 2] = newPos.z
      scale[i] = 0.001

      let color
      if (d.type === 'DELETION') {
        finalSizes[i] = 3
        color = [1, 1, 1]
      } else {
        finalSizes[i] = (Number(d.Toxicity) - 0.75) * 50
        color = [0.9, 0.23, 0.36]
      }
      colors[ 3 * i ] = color[0]
      colors[ 3 * i + 1 ] = color[1]
      colors[ 3 * i + 2 ] = color[2]
    })
    this.particleGeometry.addAttribute('position', new THREE.BufferAttribute(positions, 3))
    this.particleGeometry.addAttribute('vertexColor', new THREE.BufferAttribute(colors, 3))
    this.particleGeometry.addAttribute('scale', new THREE.BufferAttribute(scale, 1))
    this.particleGeometry.addAttribute('finalSizes', new THREE.BufferAttribute(finalSizes, 1))
    this.particleGeometry.computeBoundingSphere()
  }
}
