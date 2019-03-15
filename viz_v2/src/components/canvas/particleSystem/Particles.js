import * as THREE from 'three'
import { fibonacciSphere } from './sphereFunctions'

// Particle shader - takes scale (float) and color (vec4) variables

const particleVert = `
attribute highp float scale;
attribute float color;
attribute vec4 vertexColor;
varying vec4 vVertexColor;
void main() {
  vec4 mvPosition = modelViewMatrix * vec4( position, 1 );
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

//  if ( length( gl_PointCoord - vec2( 0.5, 0.5 ) ) > 0.475 ) discard;
// scale * ( 300.0 / - mvPosition.z );

export class Particles {
  constructor (config) {
    for (const [key, value] of Object.entries(config)) {
      this[`_${key}`] = value
    }
    this.spin = true
    this.exit = false
    this.finishedLoading = false
    this.radius = 0
    this.init()
  }

  init () {
    this.initGeometry()
    const particlesMaterial = new THREE.ShaderMaterial({
      transparent: true,
      depthWrite: true,
      vertexShader: particleVert,
      fragmentShader: particleFrag
    })

    this.particles = new THREE.Points(this.particleGeometry, particlesMaterial)

    this.loadEntryAnimation()
    this.loadExitAnimation()
    this.particleGeometry.computeBoundingSphere()
  }

  initGeometry () {
    this.particleGeometry = new THREE.BufferGeometry()

    const numPoints = this._datas.length
    const sizeWeight = this.getSizeWeight(numPoints)
    const radius = this.getRadius(numPoints)
    let positions = new Float32Array(numPoints * 3)
    let colors = new Float32Array(numPoints * 4)
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
        finalSizes[i] = sizeWeight
        color = [0.86, 1, 1]
      } else {
        finalSizes[i] = (Number(d.Toxicity) - 0.75) * sizeWeight * 20
        color = [0.86, 0.23, 0.36]
      }
      colors[ 4 * i ] = color[0]
      colors[ 4 * i + 1 ] = color[1]
      colors[ 4 * i + 2 ] = color[2]
      colors[ 4 * i + 3 ] = 1
    })

    this.particleGeometry.addAttribute('position', new THREE.BufferAttribute(positions, 3))
    this.particleGeometry.addAttribute('vertexColor', new THREE.BufferAttribute(colors, 4))
    this.particleGeometry.addAttribute('scale', new THREE.BufferAttribute(scale, 1))
    this.particleGeometry.addAttribute('finalSizes', new THREE.BufferAttribute(finalSizes, 1))
    this.particleGeometry.matrixAutoUpdate = true
  }

  resize () {
    const numPoints = this._datas.length
    const sizeWeight = this.getSizeWeight(numPoints)
    const radius = this.getRadius(numPoints)
    this._datas.forEach((d, i) => {
      const newPos = fibonacciSphere(numPoints, radius, i)
      this.particleGeometry.attributes.position.array[ 3 * i ] = newPos.x
      this.particleGeometry.attributes.position.array[3 * i + 1] = newPos.y
      this.particleGeometry.attributes.position.array[3 * i + 2] = newPos.z
      if (d.type === 'DELETION') {
        this.particleGeometry.attributes.scale.array[i] = sizeWeight
        this.particleGeometry.attributes.finalSizes.array[i] = sizeWeight
      } else {
        this.particleGeometry.attributes.scale.array[i] = (Number(d.Toxicity) - 0.75) * sizeWeight * 20
        this.particleGeometry.attributes.finalSizes.array[i] = (Number(d.Toxicity) - 0.75) * sizeWeight * 20
      }
    })
    this.particleGeometry.attributes.position.needsUpdate = true
    this.particleGeometry.attributes.scale.needsUpdate = true
  }

  getRadius (num) {
    let h = window.innerHeight
    const w = window.innerWidth
    h = h > 1100 ? h = 1000 : h
    let scale
    if (w > h) {
      scale = h / 50
    } else {
      scale = w / 30
    }
    let r = num > 280 ? scale : scale * (num / 280)
    this.radius = r < scale / 1.6 ? scale / 1.6 : r
    return this.radius
  }

  getSizeWeight (num) {
    const h = window.innerHeight
    const w = window.innerWidth
    let scale = (w > h ? h : w) / 300
    scale = scale < 1.45 ? 1.45 : scale
    const weight = num < 90 ? scale * 1.2 : scale
    return weight
  }

  loadEntryAnimation () {
    const _this = this
    _this.particles.onBeforeRender = () => {
      if (!_this.spin) return
      _this.particles.rotation.y += 0.0002

      if (_this.exit || _this.finishedLoading) return
      const attr = this.particleGeometry.attributes

      // Loading animation
      const l = _this._datas.length

      for (let i = 0; i < l; i++) {
        // CALCULATING animation delay
        let delay
        if (l < 100) {
          // Larger wait time for smaller particle systems
          if (i > l - 10) {
            delay = l - 10
          } else {
            delay = i * 1.1
          }
        } else {
          if (i > l - 100) {
            delay = l - 100
          } else {
            delay = i
          }
        }
        if (attr.scale.array[i] < attr.finalSizes.array[i] - (1 - delay / l + 0.1)) {
          attr.scale.array[i] += (1 - delay / l + 0.1)
        } else {
          attr.scale.array[i] = attr.finalSizes.array[i]
        }
        // Animation done
        if (i === l - 1) {
          const timeout = delay < 800 ? 800 : delay
          setTimeout(() => {
            _this.finishedLoading = true
          }, timeout)
        }
      }
      attr.scale.needsUpdate = true
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

  animateExit () {
    this.exit = true
  }
}
