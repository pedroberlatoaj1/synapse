import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";
import 'katex/dist/katex.min.css';

export const metadata: Metadata = {
  title: "Synapse",
  description: "SRS para estudantes de alta performance",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body className="min-h-screen bg-slate-950 text-slate-100 antialiased">
        {children}
      </body>
    </html>
  );
}
