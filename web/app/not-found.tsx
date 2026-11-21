import Link from "next/link";

export default function NotFound() {
  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col justify-center px-4 py-20 sm:px-6">
      <p className="text-sm font-semibold uppercase tracking-wide text-brand-700">Error 404</p>
      <h1 className="mt-2 text-3xl font-bold tracking-tight text-brand-950 sm:text-4xl">
        Página no encontrada
      </h1>
      <p className="mt-3 max-w-xl text-base leading-7 text-stone-600">
        El proceso o la página que buscas no existe en la cohorte consultada. Puede que el OCID esté
        mal escrito o que no esté publicado en la fuente.
      </p>
      <div className="mt-6 flex flex-wrap gap-3">
        <Link
          href="/"
          className="rounded-lg bg-brand-800 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2"
        >
          Volver a la búsqueda
        </Link>
        <a
          href="https://contratacionesabiertas.oece.gob.pe/"
          target="_blank"
          rel="noreferrer"
          className="rounded-lg border border-stone-300 bg-white px-4 py-2 text-sm font-semibold text-stone-800 hover:border-brand-400 hover:text-brand-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600"
        >
          Ir al portal oficial ↗
        </a>
      </div>
    </main>
  );
}
