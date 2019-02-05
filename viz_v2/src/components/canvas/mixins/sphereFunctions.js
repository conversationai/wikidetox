import { mapState } from 'vuex'

export default {
  name: 'SphereMixin',
  data () {
    return {
      radius: 28
    }
  },
  computed: {
    ...mapState({
      toxLength: state => state.toxicLength,
      detoxedLength: state => state.detoxedLength
    }),
    increment () { // Golden ratio * angle
      return Math.PI * (3 - Math.sqrt(5))
    },
    dataL () {
      return this.toxLength + this.detoxedLength
    }
  },
  methods: {
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
