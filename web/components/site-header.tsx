import Link from "next/link";

export function SiteHeader() {
  return (
    <header className="border-b border-brand-900/10 bg-brand-950 text-white print:hidden">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-4 py-4 sm:px-6">
        <Link
          href="/"
          className="group flex items-center gap-3 rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-300"
        >
          <span
            aria-hidden="true"
            className="flex h-10 w-10 items-center justify-center rounded-xl bg-teal-500/15 text-sm font-bold tracking-tight text-teal-200 ring-1 ring-teal-400/40"
          >
            CM
          </span>
          <span>
            <span className="block text-lg font-bold leading-tight tracking-tight">
              ContrataMYPE
            </span>
            <span className="block text-xs text-slate-300">Compras públicas explicadas</span>
          </span>
        </Link>

        <nav
          aria-label="Navegación principal"
          className="flex flex-wrap items-center gap-1 text-sm"
        >
          <Link
            href="/"
            className="rounded-lg px-3 py-2 font-medium text-slate-200 hover:bg-white/10 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-300"
          >
            Buscar oportunidades
          </Link>
          <a
            href="https://contratacionesabiertas.oece.gob.pe/"
            target="_blank"
            rel="noreferrer"
            className="rounded-lg px-3 py-2 font-medium text-slate-200 hover:bg-white/10 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-300"
          >
            Datos abiertos OECE <span aria-hidden="true">↗</span>
          </a>
        </nav>
      </div>
    </header>
  );
}
