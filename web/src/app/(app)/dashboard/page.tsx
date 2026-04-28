import { InlineMath } from "react-katex";

const decks = [
  {
    title: "trigonometria",
    description: "Identidades, circulo trigonometrico e funcoes seno/cosseno.",
    cards: 32,
    due: 8,
  },
  {
    title: "botanica",
    description: "Tecidos vegetais, fotossintese e ciclos reprodutivos.",
    cards: 24,
    due: 5,
  },
  {
    title: "eletromagnetismo",
    description: "Campos, forcas, fluxo magnetico e circuitos.",
    cards: 41,
    due: 13,
    equation: "F = q(E + v \\times B)",
  },
];

export default function DashboardPage() {
  return (
    <main className="min-h-screen bg-zinc-950 text-zinc-50">
      <div className="flex min-h-screen">
        <aside className="hidden w-72 shrink-0 border-r border-zinc-800 bg-zinc-950 px-8 py-10 lg:block">
          <p className="text-4xl font-bold tracking-tight text-white">Synapse</p>

          <nav className="mt-12 space-y-2 text-sm font-medium text-zinc-400">
            <a
              className="block rounded-xl bg-zinc-900 px-4 py-3 text-white"
              href="/dashboard"
            >
              Meus decks
            </a>
            <a
              className="block rounded-xl px-4 py-3 transition hover:bg-zinc-900 hover:text-white"
              href="/review/eletromagnetismo"
            >
              Revisao
            </a>
          </nav>
        </aside>

        <section className="flex min-w-0 flex-1 flex-col">
          <header className="flex items-center justify-between border-b border-zinc-800 px-6 py-5 lg:hidden">
            <p className="text-4xl font-bold tracking-tight text-white">Synapse</p>
            <a
              className="rounded-full border border-zinc-800 px-4 py-2 text-sm font-medium text-zinc-300"
              href="/review/eletromagnetismo"
            >
              Revisao
            </a>
          </header>

          <div className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-6 py-10">
            <div className="flex flex-col gap-2">
              <p className="text-sm font-medium uppercase tracking-wide text-zinc-500">
                Biblioteca
              </p>
              <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
                Meus decks
              </h1>
            </div>

            <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
              {decks.map((deck) => (
                <article
                  key={deck.title}
                  className="rounded-xl border border-zinc-800 bg-zinc-900 p-6 shadow-lg shadow-black/20"
                >
                  <div className="flex min-h-56 flex-col justify-between gap-8">
                    <div className="space-y-4">
                      <div className="flex items-start justify-between gap-4">
                        <h2 className="text-2xl font-semibold capitalize tracking-tight text-white">
                          {deck.title}
                        </h2>
                        <span className="rounded-full border border-zinc-700 px-3 py-1 text-xs font-semibold text-zinc-300">
                          {deck.due} hoje
                        </span>
                      </div>

                      <p className="text-sm leading-6 text-zinc-400">
                        {deck.description}
                      </p>

                      {deck.equation ? (
                        <div className="rounded-lg border border-zinc-800 bg-zinc-950 px-4 py-3 text-center text-zinc-100">
                          <InlineMath math={deck.equation} />
                        </div>
                      ) : null}
                    </div>

                    <div className="flex items-center justify-between border-t border-zinc-800 pt-4">
                      <span className="text-sm text-zinc-500">
                        {deck.cards} cards
                      </span>
                      <a
                        className="rounded-lg bg-white px-4 py-2 text-sm font-semibold text-zinc-950 transition hover:bg-zinc-200"
                        href={`/review/${deck.title}`}
                      >
                        Revisar
                      </a>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
