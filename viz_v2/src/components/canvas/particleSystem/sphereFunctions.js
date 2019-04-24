/*
Copyright 2019 Google Inc.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

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
