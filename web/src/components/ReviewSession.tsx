"use client";

import { useMemo, useState } from "react";

import MathCard from "./MathCard";

export type ReviewCard = {
  id: string;
  deck_id: string;
  front: string;
  back: string;
  state: string;
  due_at: string;
};

type ReviewSessionProps = {
  initialCards: ReviewCard[];
};

type RatingValue = 1 | 2 | 3 | 4;

const ratingButtons: Array<{
  label: string;
  rating: RatingValue;
  className: string;
}> = [
  {
    label: "errei",
    rating: 1,
    className:
      "border-red-500/40 bg-red-500/15 text-red-200 hover:bg-red-500/25",
  },
  {
    label: "dificil",
    rating: 2,
    className:
      "border-amber-500/40 bg-amber-500/15 text-amber-200 hover:bg-amber-500/25",
  },
  {
    label: "bom",
    rating: 3,
    className:
      "border-blue-500/40 bg-blue-500/15 text-blue-200 hover:bg-blue-500/25",
  },
  {
    label: "facil",
    rating: 4,
    className:
      "border-green-500/40 bg-green-500/15 text-green-200 hover:bg-green-500/25",
  },
];

function createClientEventId() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }

  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;

  const hex = Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0"));
  return [
    hex.slice(0, 4).join(""),
    hex.slice(4, 6).join(""),
    hex.slice(6, 8).join(""),
    hex.slice(8, 10).join(""),
    hex.slice(10, 16).join(""),
  ].join("-");
}

export default function ReviewSession({ initialCards }: ReviewSessionProps) {
  const [cards, setCards] = useState(initialCards);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showBack, setShowBack] = useState(false);
  const [startedAt, setStartedAt] = useState(() => Date.now());
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const currentCard = cards[currentIndex] ?? null;
  const progressLabel = useMemo(() => {
    if (!currentCard) {
      return "0 de 0";
    }
    return `${currentIndex + 1} de ${cards.length}`;
  }, [cards.length, currentCard, currentIndex]);

  async function submitRating(rating: RatingValue) {
    if (!currentCard || isSubmitting) {
      return;
    }

    setError(null);
    setIsSubmitting(true);

    try {
      const response = await fetch("/api/reviews", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          card_id: currentCard.id,
          client_event_id: createClientEventId(),
          device_id: "web",
          client_ts: new Date().toISOString(),
          rating,
          duration_ms: Math.max(0, Date.now() - startedAt),
        }),
      });

      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.detail ?? "Nao foi possivel salvar a revisao.");
      }

      const nextCards = cards.filter((card) => card.id !== currentCard.id);
      setCards(nextCards);
      setCurrentIndex((index) => {
        if (nextCards.length === 0) {
          return 0;
        }
        return Math.min(index, nextCards.length - 1);
      });
      setShowBack(false);
      setStartedAt(Date.now());
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "Nao foi possivel salvar a revisao.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  if (!currentCard) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <div className="w-full max-w-xl rounded-2xl border border-zinc-800 bg-zinc-900 p-8 text-center shadow-xl shadow-black/30">
          <p className="text-sm font-medium uppercase tracking-wide text-zinc-500">
            Revisao concluida
          </p>
          <h2 className="mt-4 text-3xl font-bold tracking-tight text-white">
            Tudo revisado por agora.
          </h2>
          <p className="mt-3 text-sm leading-6 text-zinc-400">
            A fila deste deck esta vazia. Volte mais tarde quando novos cards
            estiverem devidos.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-8">
      <div className="w-full max-w-3xl">
        <p className="mb-3 text-sm font-medium text-zinc-500">
          {progressLabel}
        </p>
        <MathCard
          front={currentCard.front}
          back={currentCard.back}
          showBack={showBack}
        />
      </div>

      {error ? (
        <p className="w-full max-w-3xl rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
          {error}
        </p>
      ) : null}

      {showBack ? (
        <div className="grid w-full max-w-3xl grid-cols-2 gap-3 sm:grid-cols-4">
          {ratingButtons.map((button) => (
            <button
              key={button.rating}
              className={`rounded-xl border px-5 py-4 text-base font-bold lowercase transition disabled:cursor-not-allowed disabled:opacity-60 ${button.className}`}
              type="button"
              disabled={isSubmitting}
              onClick={() => submitRating(button.rating)}
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
  );
}
