"use client";

import { useState } from "react";

import MathCard from "../../../../components/MathCard";

const cards = [
  {
    front: "\\text{Qual e a relacao fundamental do Teorema de Pitagoras?}",
    back: "a^2 + b^2 = c^2",
  },
  {
    front: "\\text{Como calcular a forca eletrica em uma carga?}",
    back: "\\vec{F} = q\\vec{E}",
  },
  {
    front: "\\text{Qual e a derivada de } x^2?",
    back: "\\frac{d}{dx}x^2 = 2x",
  },
];

const reviewButtons = [
  {
    label: "errei",
    className:
      "border-red-500/40 bg-red-500/15 text-red-200 hover:bg-red-500/25",
  },
  {
    label: "dificil",
    className:
      "border-amber-500/40 bg-amber-500/15 text-amber-200 hover:bg-amber-500/25",
  },
  {
    label: "bom",
    className:
      "border-blue-500/40 bg-blue-500/15 text-blue-200 hover:bg-blue-500/25",
  },
  {
    label: "facil",
    className:
      "border-green-500/40 bg-green-500/15 text-green-200 hover:bg-green-500/25",
  },
];

export default function ReviewPage() {
  const [cardIndex, setCardIndex] = useState(0);
  const [showBack, setShowBack] = useState(false);
  const currentCard = cards[cardIndex];

  function goToNextCard() {
    setCardIndex((current) => (current + 1) % cards.length);
    setShowBack(false);
  }

  return (
    <main className="min-h-screen bg-zinc-950 px-6 py-8 text-zinc-50">
      <section className="mx-auto flex min-h-[calc(100vh-4rem)] w-full max-w-5xl flex-col">
        <header className="mb-8">
          <h1 className="text-4xl font-bold tracking-tight text-white">
            Revisao
          </h1>
        </header>

        <div className="flex flex-1 flex-col items-center justify-center gap-8">
          <MathCard
            front={currentCard.front}
            back={currentCard.back}
            showBack={showBack}
          />

          {showBack ? (
            <div className="grid w-full max-w-3xl grid-cols-2 gap-3 sm:grid-cols-4">
              {reviewButtons.map((button) => (
                <button
                  key={button.label}
                  className={`rounded-xl border px-5 py-4 text-base font-bold lowercase transition ${button.className}`}
                  type="button"
                  onClick={goToNextCard}
                >
                  {button.label}
                </button>
              ))}
            </div>
          ) : (
            <button
              className="w-full max-w-3xl rounded-xl bg-white px-6 py-4 text-lg font-bold text-zinc-950 shadow-lg shadow-black/20 transition hover:bg-zinc-200"
              type="button"
              onClick={() => setShowBack(true)}
            >
              Mostrar Resposta
            </button>
          )}
        </div>
      </section>
    </main>
  );
}
