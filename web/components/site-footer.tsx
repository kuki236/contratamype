import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="mt-16 border-t border-stone-200 bg-white print:hidden">
      <div className="mx-auto grid max-w-6xl gap-6 px-4 py-10 text-sm text-stone-600 sm:px-6 md:grid-cols-[2fr_1fr]">
        <div>
          <p className="font-semibold text-brand-950">ContrataMYPE</p>
          <p className="mt-2 max-w-2xl leading-6">
            La etiqueta MYPE es una{" "}
            <strong>heurística de compatibilidad MYPE, no elegibilidad legal</strong>. Las bases del
            proceso son la fuente vinculante. Verifica siempre en el portal oficial.
          </p>
          <p className="mt-3 max-w-2xl leading-6">
            Datos: OECE — Portal de Contrataciones Abiertas, estándar OCDS, redistribuidos bajo CC
            BY 4.0. ContrataMYPE no está afiliado al OECE.
          </p>
        </div>
        <nav aria-label="Enlaces de la fuente" className="space-y-2">
          <Link href="/" className="block font-medium text-brand-800 hover:underline">
            Buscar oportunidades
          </Link>
          <a
            href="https://contratacionesabiertas.oece.gob.pe/"
            target="_blank"
            rel="noreferrer"
            className="block font-medium text-brand-800 hover:underline"
          >
            Portal de Contrataciones Abiertas ↗
          </a>
          <a
            href="https://data.open-contracting.org/es/publication/135"
            target="_blank"
            rel="noreferrer"
            className="block font-medium text-brand-800 hover:underline"
          >
            Datos OCDS (OCP) ↗
          </a>
        </nav>
      </div>
    </footer>
  );
}
