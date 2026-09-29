import { type ReactNode, useEffect, useRef } from "react";
import { Monogram } from "./series/Monogram";

/**
 * The note from me, in holographic foil like a trading card. The border's
 * colours turn slowly and a sheen follows the pointer, or the tilt of a
 * phone. The words sit on a solid panel, so the shine never costs contrast,
 * and all of it stands still for anyone who has asked for reduced motion.
 */
export function FoilNote({ children }: { children: ReactNode }) {
  const el = useRef<HTMLElement>(null);

  useEffect(() => {
    const node = el.current;
    if (!node || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const sheen = (f: number) =>
      node.style.setProperty("--sheen", `${Math.round(140 - Math.min(1, Math.max(0, f)) * 160)}%`);
    const move = (e: PointerEvent) => {
      const r = node.getBoundingClientRect();
      sheen((e.clientX - r.left) / r.width);
    };
    const tilt = (e: DeviceOrientationEvent) => {
      if (e.gamma != null) sheen((e.gamma + 30) / 60);
    };
    node.addEventListener("pointermove", move);
    addEventListener("deviceorientation", tilt);
    return () => {
      node.removeEventListener("pointermove", move);
      removeEventListener("deviceorientation", tilt);
    };
  }, []);

  return (
    <aside ref={el} className="foil" aria-label="A note from Finn">
      <div className="inner">
        <div className="who">
          <Monogram size={18} label={null} />A note from Finn
        </div>
        <p>{children}</p>
        <div className="sig">Finn</div>
      </div>
    </aside>
  );
}
