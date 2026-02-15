export const sim = {
  state: null,
  running: false,
  started: false,

  initialDistance: null,
  initialSpeed: null,

  missed: false,
  startX: null,
  freeze: false,

  // joystick state
  joyActive: false,
  joyVec: { x: 0, y: 0 },

  // camera
  renderCam: { cx: 0, cy: 0, zoom: 1.0 },

  // trail
  trail: [],
};

export function setState(newState) {
  sim.state = newState;
}
