import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

// Inter pro corpo — fonte clássica de interface, mais legível e polida que a
// Geist default do scaffold. Variable font (todos os pesos num único arquivo).
const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin"],
  display: "swap",
});

// JetBrains Mono pro código / preview JSON — mais legível que Geist Mono.
const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "InsurMind — Chatbot Porto Inseguro",
  description:
    "Chatbot acadêmico de seguro auto da seguradora fictícia Porto Inseguro. " +
    "Curso I2A2 InsurMinds, Atividade Obrigatória 2.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="pt-BR"
      className={`${inter.variable} ${jetbrainsMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-zinc-50 text-[15px]">
        {children}
      </body>
    </html>
  );
}
