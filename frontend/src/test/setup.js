import { expect, afterEach, beforeAll } from 'vitest'
import { cleanup } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'

// Mock localStorage
beforeAll(() => {
  const localStorageMock = {
    getItem: (key) => localStorageMock[key] || null,
    setItem: (key, value) => {
      localStorageMock[key] = value
    },
    removeItem: (key) => {
      delete localStorageMock[key]
    },
    clear: () => {
      Object.keys(localStorageMock).forEach(key => {
        if (key !== 'getItem' && key !== 'setItem' && key !== 'removeItem' && key !== 'clear') {
          delete localStorageMock[key]
        }
      })
    }
  }
  global.localStorage = localStorageMock
})

// Cleanup after each test
afterEach(() => {
  cleanup()
  if (global.localStorage && global.localStorage.clear) {
    global.localStorage.clear()
  }
})
