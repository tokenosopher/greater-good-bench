// In-memory session state. Nothing is stored: the page must work in a sandbox with no storage.
import { guessCountry } from "./numbers.js";

const listeners = new Set();

export const state = {
  /** When the visitor arrived. Drives the survival clock and the closing message. */
  arrived: performance.now(),
  /** Ids of finished drills. */
  done: new Set(),
  country: guessCountry(),
  guessed: true,
  sound: true,
  /** Results worth showing on the closing card. */
  results: {},
};

/** The number to dial, e.g. "112". */
export const num = () => state.country.n;

export function subscribe(fn) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

export function emit() {
  for (const fn of [...listeners]) fn(state);
}

export function setCountry(country) {
  state.country = country;
  state.guessed = false;
  emit();
}

export function markDone(id) {
  state.done.add(id);
  emit();
}

export function secondsHere() {
  return (performance.now() - state.arrived) / 1000;
}
