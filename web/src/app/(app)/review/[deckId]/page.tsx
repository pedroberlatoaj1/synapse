import { redirect } from "next/navigation";

import ReviewSession, {
  type ReviewCard,
} from "../../../../components/ReviewSession";
import { ApiError, apiFetch } from "../../../../lib/api";

type ReviewPageProps = {
  params: Promise<{
    deckId: string;
  }>;
};

async function getReviewQueue(deckId: string) {
  try {
    return await apiFetch<ReviewCard[]>(
      `/reviews/queue?deck_id=${encodeURIComponent(deckId)}`,
      {
        cache: "no-store",
      },
    );
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      redirect("/login");
    }
    throw error;
  }
}

export default async function ReviewPage({ params }: ReviewPageProps) {
  const { deckId } = await params;
  const cards = await getReviewQueue(deckId);

  return (
    <main className="min-h-screen bg-zinc-950 px-6 py-8 text-zinc-50">
      <section className="mx-auto flex min-h-[calc(100vh-4rem)] w-full max-w-5xl flex-col">
        <header className="mb-8">
          <h1 className="text-4xl font-bold tracking-tight text-white">
            Revisao
          </h1>
        </header>

        <ReviewSession initialCards={cards} />
      </section>
    </main>
  );
}
