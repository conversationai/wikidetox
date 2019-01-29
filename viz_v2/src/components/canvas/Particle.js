import * as THREE from 'three'

export class Particle {
  constructor (config) {
    for (const [key, value] of Object.entries(config)) {
      this[key] = value
    }
    this.createMesh()
  }
  createMesh () {
    this.mesh = new THREE.Mesh(this.geometry, new THREE.MeshBasicMaterial({
      transparent: true,
      opacity: 0.9,
      depthTest: false,
      precision: 'lowp',
      color: this.color
    }))
    this.mesh.position.x = this.x
    this.mesh.position.y = this.y
    this.mesh.position.z = this.z
    this.mesh.scale.set(this.size, this.size, this.size)
    this.mesh.name = this.commentID
    this.group.add(this.mesh)
    this.animationGroup.add(this.mesh)
  }
}
