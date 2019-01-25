import {
  mapGetters
} from 'vuex'

export default {
  name: 'SphereMixin',
  data () {
    return {
      radius: 28
    }
  },
  computed: {
    ...mapGetters({
      dataL: 'getDatalength'
    }),
    increment () { // Golden ratio * angle
      return Math.PI * (3 - Math.sqrt(5))
    }
  },
  methods: {
    // randomSpherePoint () {
    //   const u = Math.random()
    //   const v = Math.random()
    //   const theta = 2 * Math.PI * u
    //   const phi = Math.acos(2 * v - 1)
    //   const x = this.radius * Math.sin(phi) * Math.cos(theta)
    //   const y = this.radius * Math.sin(phi) * Math.sin(theta)
    //   const z = this.radius * Math.cos(phi)
    //   return {
    //     x: x,
    //     y: y,
    //     z: z
    //   }
    // },
    // diatanceTo (a, b) {
    //     const dx = a.x - b.x
    //     const dy = a.y - b.y
    //     const dz = a.z - b.z

    //     return Math.sqrt(dx * dx + dy * dy + dz * dz)
    // },
    fibonacciSphere (i) {
      const offset = 2 / this.dataL
      const offsetHalf = offset / 2
      const y = (((i * offset) - 1) + offsetHalf)
      const r = Math.sqrt(1 - y * y)
      const phi = (i % this.dataL) * this.increment
      const x = Math.cos(phi) * r
      const z = Math.sin(phi) * r
      return {
        x: x * this.radius,
        y: y * this.radius,
        z: z * this.radius
      }
    }
  }
}
