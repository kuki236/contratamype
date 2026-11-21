"use client";

import { useEffect } from "react";

export default function ErrorPage({ error, retry }: { error: unknown; retry: () => void }) {
  useEffect(() => {
    console.error("Error al cargar la página", error);
  }, [error]);

  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col justify-center px-4 py-20 sm:px-6">
      <p className="text-sm font-semibold uppercase tracking-wide text-brand-700">
        Servicio no disponible
      </p>
      <h1 className="mt-2 text-3xl font-bold tracking-tight text-brand-950 sm:text-4xl">
        No pudimos cargar las oportunidades
      </h1>
      <p className="mt-3 max-w-xl text-base leading-7 text-stone-600">
        La API local no respondió. Verifica que esté en ejecución y que{" "}
        <code className="rounded bg-stone-100 px-1.5 py-0.5 text-sm">CONTRATAMYPE_API_URL</code>{" "}
        apunte al puerto correcto.
      </p>
      <div className="mt-6">
        <button
          type="button"
          onClick={retry}
          className="rounded-lg bg-brand-800 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2"
        >
          Reintentar
        </button>
      </div>
    </main>
  );
}
