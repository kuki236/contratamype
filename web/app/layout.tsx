import type { Metadata } from "next";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "ContrataMYPE — Compras públicas explicadas",
    template: "%s · ContrataMYPE",
  },
  description:
    "Busca oportunidades de compras públicas en Perú, revisa datos oficiales y descarga un checklist de participación para tu MYPE.",
  applicationName: "ContrataMYPE",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body className="flex min-h-screen flex-col">
        <a href="#contenido" className="skip-link">
          Saltar al contenido
        </a>
        <SiteHeader />
        <div id="contenido" className="flex flex-1 flex-col">
          {children}
        </div>
        <SiteFooter />
      </body>
    </html>
  );
}
