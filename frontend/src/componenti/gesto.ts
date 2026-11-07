import type { MouseEvent } from "react"

/** A click on a delivery `<a href="#">`: no navigation, then the action if there is one. */
export const gesto =
  (f?: () => void) =>
  (e: MouseEvent): void => {
    e.preventDefault()
    f?.()
  }
