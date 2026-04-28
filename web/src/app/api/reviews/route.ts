import { NextResponse } from "next/server";

import { ApiError, apiFetch } from "../../../lib/api";

type ReviewPayload = {
  card_id: string;
  client_event_id: string;
  device_id: string;
  client_ts: string;
  rating: 1 | 2 | 3 | 4;
  duration_ms: number;
};

const ratingMap: Record<ReviewPayload["rating"], string> = {
  1: "again",
  2: "hard",
  3: "good",
  4: "easy",
};

export async function POST(request: Request) {
  const payload = (await request.json()) as ReviewPayload;
  const backendRating = ratingMap[payload.rating];

  if (!backendRating) {
    return NextResponse.json(
      { detail: "Invalid review rating" },
      { status: 400 },
    );
  }

  try {
    const response = await apiFetch("/reviews", {
      method: "POST",
      body: JSON.stringify({
        ...payload,
        rating: backendRating,
      }),
      cache: "no-store",
    });

    return NextResponse.json(response);
  } catch (error) {
    if (error instanceof ApiError) {
      return NextResponse.json(
        error.body ?? { detail: error.message },
        { status: error.status },
      );
    }

    return NextResponse.json(
      { detail: "Review submission failed" },
      { status: 500 },
    );
  }
}
