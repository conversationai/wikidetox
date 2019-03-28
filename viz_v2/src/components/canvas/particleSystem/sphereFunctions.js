const increment = Math.PI * (3 - Math.sqrt(5))

const fibonacciSphere = (dataLength, radius, i) => {
  const offset = 2 / dataLength
  const offsetHalf = offset / 2
  const y = (((i * offset) - 1) + offsetHalf)
  const r = Math.sqrt(1 - y * y)
  const phi = (i % dataLength) * increment
  const x = Math.cos(phi) * r
  const z = Math.sin(phi) * r
  return {
    x: x * radius,
    y: y * radius,
    z: z * radius
  }
}

export { fibonacciSphere }
