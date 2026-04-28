"use client";

import { BlockMath, InlineMath } from "react-katex";

type MathCardProps = {
  front: string;
  back: string;
};

export default function MathCard({ front, back }: MathCardProps) {
  return (
    <article className="rounded-lg border border-slate-200 bg-white p-6 text-slate-950 shadow-sm">
      <div className="space-y-4">
        <div className="border-b border-slate-200 pb-4">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Frente
          </p>
          <div className="text-lg font-medium">
            <InlineMath math={front} />
          </div>
        </div>

        <div>
          <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Verso
          </p>
          <div className="overflow-x-auto rounded-md bg-slate-50 px-4 py-5">
            <BlockMath math={back} />
          </div>
        </div>
      </div>
    </article>
  );
}
