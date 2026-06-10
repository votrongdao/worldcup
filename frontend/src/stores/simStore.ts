// Live frame ring buffer feeding the canvas renderer.
import type { Frame } from "../api/types";

type Listener = () => void;
class SimStore {
  private buf: Frame[] = [];
  private listeners = new Set<Listener>();
  pushFrame = (f: Frame) => { this.buf.push(f); if (this.buf.length > 240) this.buf.shift(); this.emit(); };
  current = () => this.buf[this.buf.length - 1];
  frames = () => this.buf;
  subscribe = (l: Listener) => { this.listeners.add(l); return () => this.listeners.delete(l); };
  private emit() { this.listeners.forEach((l) => l()); }
}
const store = new SimStore();
export function useSimStore<T>(sel: (s: SimStore) => T): T { return sel(store); }
