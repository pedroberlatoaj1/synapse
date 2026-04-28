import MathCard from "../../../components/MathCard";

const mathCards = [
  {
    front: "\\text{Teorema de Pitagoras}",
    back: "a^2 + b^2 = c^2",
  },
  {
    front: "\\text{Equacao de Schrodinger dependente do tempo}",
    back: "i\\hbar\\frac{\\partial}{\\partial t}\\Psi(\\mathbf{r},t)=\\hat{H}\\Psi(\\mathbf{r},t)",
  },
];

export default function DashboardPage() {
  return (
    <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-100">
      <section className="mx-auto flex w-full max-w-5xl flex-col gap-8">
        <header>
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            Dashboard Synapse
          </h1>
        </header>

        <div className="grid gap-4 md:grid-cols-2">
          {mathCards.map((card) => (
            <MathCard key={card.front} front={card.front} back={card.back} />
          ))}
        </div>
      </section>
    </main>
  );
}
