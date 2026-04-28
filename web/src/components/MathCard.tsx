"use client";

import { BlockMath, InlineMath } from "react-katex";

type MathCardProps = {
  front: string;
  back: string;
  showBack?: boolean;
};

export default function MathCard({ front, back, showBack = false }: MathCardProps) {
  return (
    <article className="flex min-h-[400px] w-full max-w-3xl items-center justify-center rounded-2xl border border-zinc-800 bg-zinc-900 p-8 text-center shadow-xl shadow-black/30">
      <div className="w-full space-y-8">
        <div className="space-y-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
            Frente
          </p>
          <div className="text-3xl font-semibold leading-relaxed text-white sm:text-4xl">
            <InlineMath math={front} />
          </div>
        </div>

        {showBack ? (
          <div className="border-t border-zinc-800 pt-8">
            <p className="mb-4 text-xs font-semibold uppercase tracking-wide text-zinc-500">
              Verso
            </p>
            <div className="overflow-x-auto rounded-xl bg-zinc-950 px-4 py-6 text-white">
              <BlockMath math={back} />
            </div>
          </div>
        ) : null}
      </div>
    </article>
  );
}
