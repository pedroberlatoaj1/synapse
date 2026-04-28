"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.detail ?? "Nao foi possivel entrar.");
      }

      router.replace("/dashboard");
      router.refresh();
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "Nao foi possivel entrar.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-zinc-950 px-6 py-10 text-zinc-50">
      <section className="w-full max-w-md">
        <div className="mb-10">
          <p className="text-5xl font-bold tracking-tight text-white">
            Synapse
          </p>
          <h1 className="mt-8 text-3xl font-semibold tracking-tight text-white">
            Entrar
          </h1>
        </div>

        <form
          className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6 shadow-xl shadow-black/30"
          onSubmit={handleSubmit}
        >
          <div className="space-y-5">
            <label className="block">
              <span className="text-sm font-medium text-zinc-300">E-mail</span>
              <input
                className="mt-2 w-full rounded-xl border border-zinc-800 bg-zinc-950 px-4 py-3 text-zinc-50 outline-none transition placeholder:text-zinc-600 focus:border-zinc-500"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="voce@synapse.dev"
                required
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium text-zinc-300">Senha</span>
              <input
                className="mt-2 w-full rounded-xl border border-zinc-800 bg-zinc-950 px-4 py-3 text-zinc-50 outline-none transition placeholder:text-zinc-600 focus:border-zinc-500"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Sua senha"
                required
              />
            </label>
          </div>

          {error ? (
            <p className="mt-5 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
              {error}
            </p>
          ) : null}

          <button
            className="mt-6 w-full rounded-xl bg-white px-5 py-3 font-bold text-zinc-950 transition hover:bg-zinc-200 disabled:cursor-not-allowed disabled:opacity-60"
            type="submit"
            disabled={isSubmitting}
          >
            {isSubmitting ? "Entrando..." : "Entrar"}
          </button>
        </form>
      </section>
    </main>
  );
}
