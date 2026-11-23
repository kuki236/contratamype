import { expect, test } from "@playwright/test";
import { inflateSync } from "node:zlib";

function decodePdfStreams(buffer: Buffer): string {
  const raw = buffer.toString("latin1");
  const parts: string[] = [];
  for (const match of raw.matchAll(/stream\r?\n([\s\S]*?)\r?\nendstream/g)) {
    const chunk = Buffer.from(match[1], "latin1");
    let stream: string;
    try {
      stream = inflateSync(chunk).toString("latin1");
    } catch {
      stream = chunk.toString("latin1");
    }
    parts.push(
      stream.replace(/<([0-9A-Fa-f]+)>/g, (_, hex: string) =>
        Buffer.from(hex, "hex").toString("latin1"),
      ),
    );
  }
  return parts.join("\n");
}

test.describe("parámetros de búsqueda fuera de rango", () => {
  test("trunca q a 200 caracteres en vez de romper con 422", async ({ page }) => {
    const longQuery = "a".repeat(201);
    const response = await page.goto(`/?q=${longQuery}`);

    expect(response?.status()).toBe(200);
    await expect(page.getByLabel("Buscar por texto")).toHaveAttribute("maxlength", "200");
    await expect(page.getByLabel("Buscar por texto")).toHaveValue("a".repeat(200));
    await expect(page.getByTestId("empty-state")).toBeVisible();
    await expect(page.getByText("No pudimos cargar las oportunidades")).toHaveCount(0);
  });

  test("no copia montos inválidos al enlace de la página siguiente", async ({ page }) => {
    await page.goto("/?min_amount=abc&mype_only=0");
    await expect(page.getByTestId("opportunity-card")).toHaveCount(20);

    const next = page.getByRole("link", { name: /Siguiente/ });
    await expect(next).toHaveAttribute("href", "/?mype_only=0&page=2");
    await next.click();

    await expect(page).toHaveURL(/page=2/);
    await expect(page).not.toHaveURL(/min_amount/);
    await expect(page.getByTestId("opportunity-card")).toHaveCount(17);
    await expect(page.getByRole("heading", { level: 2, name: "37 oportunidades" })).toBeVisible();

    await page.goto("/?year=2025&min_amount=abc&mype_only=0");
    const yearNext = page.getByRole("link", { name: /Siguiente/ });
    await expect(yearNext).toHaveAttribute("href", "/?year=2025&mype_only=0&page=2");
    await yearNext.click();

    await expect(page).toHaveURL(/year=2025/);
    await expect(page).toHaveURL(/page=2/);
    await expect(page.getByTestId("opportunity-card")).toHaveCount(16);
    await expect(page.getByRole("heading", { level: 2, name: "36 oportunidades" })).toBeVisible();
  });

  test("muestra página fuera de rango con enlace a la página 1", async ({ page }) => {
    const response = await page.goto("/?page=999999999999999999");

    expect(response?.status()).toBe(200);
    await expect(page.getByTestId("page-out-of-range")).toBeVisible();
    await expect(page.getByText("Página fuera de rango")).toBeVisible();
    await page.getByRole("link", { name: "Ir a la página 1" }).click();
    await expect(page).not.toHaveURL(/page=/);
    await expect(page.getByTestId("opportunity-card")).toHaveCount(8);

    await page.goto("/?year=2024&mype_only=0&page=5");
    await expect(page.getByTestId("page-out-of-range")).toBeVisible();
    await expect(page.getByRole("link", { name: "Ir a la página 1" })).toHaveAttribute(
      "href",
      "/?year=2024&mype_only=0",
    );
  });

  test("la API rechaza páginas enormes con 422, no con 500", async ({ request }) => {
    const apiPort = process.env.CONTRATAMYPE_API_PORT ?? "8010";
    const response = await request.get(
      `http://127.0.0.1:${apiPort}/opportunities?page=999999999999999999`,
    );

    expect(response.status()).toBe(422);
  });
});

test.describe("estado vacío y etiquetas", () => {
  test("ofrece ver todas las oportunidades cuando el filtro MYPE oculta resultados", async ({
    page,
  }) => {
    await page.goto("/?year=2025&q=saneamiento");

    await expect(page.getByTestId("empty-state")).toBeVisible();
    const showAll = page.getByRole("link", { name: "Ver todas las oportunidades" });
    await expect(showAll).toHaveAttribute("href", "/?q=saneamiento&year=2025&mype_only=0");
    await showAll.click();

    await expect(page).toHaveURL(/year=2025/);
    await expect(page.getByTestId("opportunity-card")).toHaveCount(1);
    await expect(page.getByText("Obra de saneamiento rural")).toBeVisible();
  });

  test("traduce estados OCDS y marca el texto crudo de la fuente", async ({ page }) => {
    await page.goto("/opportunities/ocds-test-0001");
    await expect(page.getByRole("cell", { name: "Vigente" })).toHaveCount(2);

    await page.goto("/opportunities/ocds-test-0002");
    await expect(page.getByText("En evaluación (fuente)", { exact: true })).toBeVisible();
  });

  test("etiqueta la incompatibilidad MYPE como heurística, no como impedimento", async ({
    page,
  }) => {
    await page.goto("/opportunities/ocds-test-0003");

    await expect(page.getByTestId("mype-badge")).toHaveText("No marcada compatible");
    await expect(
      page.getByText("heurística de compatibilidad MYPE, no elegibilidad legal").first(),
    ).toBeVisible();
  });
});

test.describe("calidad de datos visible", () => {
  test("suma adjudicaciones sin proveedor y contratos sin vínculo a las alertas", async ({
    page,
  }) => {
    await page.goto("/opportunities/ocds-test-0003");
    const notes = page.getByRole("note");
    await expect(notes).toContainText("Adjudicación sin proveedor identificado.");
    await expect(notes).toContainText("La fuente registra S/ 0.00 como monto (no informado útil).");

    await page.goto("/opportunities/ocds-test-0004");
    const danglingNotes = page.getByRole("note");
    await expect(danglingNotes).toContainText("Contrato sin adjudicación vinculada.");
    await expect(
      page.getByRole("cell", { name: "Contrato sin adjudicación vinculada." }),
    ).toBeVisible();
  });
});

test.describe("checklist y PDF", () => {
  test("mantiene los 9 pasos, una cita por paso y el disclaimer", async ({ page }) => {
    await page.goto("/opportunities/ocds-test-0001/checklist");

    const items = page.getByTestId("checklist-item");
    await expect(items).toHaveCount(9);
    for (const item of await items.all()) {
      await expect(item.getByText("Fuente:", { exact: false })).toBeVisible();
    }
    await expect(page.getByTestId("disclaimer")).toContainText(
      "heurística de compatibilidad MYPE, no elegibilidad legal",
    );
  });

  test("usa S/ 0.00 (no informado útil) en el checklist de monto cero", async ({ page }) => {
    await page.goto("/opportunities/ocds-test-0003/checklist");

    await expect(page.getByText("S/ 0.00 (no informado útil)", { exact: true })).toBeVisible();
    await expect(page.getByTestId("checklist-warnings")).toContainText(
      "La fuente registra S/ 0.00 como monto (no informado útil).",
    );
    await expect(page.getByTestId("mype-badge")).toHaveText("No marcada compatible");
  });

  test("el PDF del caso incompleto incluye monto, categoría, fuentes y disclaimer", async ({
    request,
  }) => {
    const response = await request.get("/opportunities/ocds-test-0003/checklist/pdf");

    expect(response.status()).toBe(200);
    const text = decodePdfStreams(await response.body());
    expect(text).toContain("ContrataMYPE");
    expect(text).toContain("no informado útil");
    expect(text).toContain("Obras");
    expect(text).toContain("no marcada compatible");
    expect(text).toContain("tenders.amount_pen");
    expect(text).toMatch(/elegibilidad\s+legal/);
  });
});

test.describe("explicador por plantilla", () => {
  test("expone Qué revisar y Datos faltantes con citas y disclaimer", async ({ page }) => {
    await page.goto("/opportunities/ocds-test-0002");

    const points = page.getByTestId("explainer-point");
    const review = points.filter({ hasText: "Qué revisar" });
    const missing = points.filter({ hasText: "Datos faltantes" });

    await expect(review).toHaveCount(1);
    await expect(review).toContainText("bases integradas");
    await expect(review).toContainText("Fuente:");
    await expect(missing).toHaveCount(1);
    await expect(missing).toContainText("Descripción del objeto");
    await expect(missing).toContainText("Adjudicaciones");
    await expect(missing).toContainText("Contratos");
    await expect(missing).toContainText("Fuente:");
    await expect(page.getByTestId("explainer-disclaimer")).toContainText("no elegibilidad legal");

    const explainerText = (await points.allInnerTexts()).join(" ");
    expect(explainerText).not.toMatch(/\b(elegible|puede postular|califica)\b/i);
  });
});

test.describe("contrato de la API por año", () => {
  test("agrega cohortes por defecto y filtra 2024/2025 con conteos exactos", async ({
    request,
  }) => {
    const apiPort = process.env.CONTRATAMYPE_API_PORT ?? "8010";
    const base = `http://127.0.0.1:${apiPort}`;

    const meta = await (await request.get(`${base}/meta`)).json();
    expect(meta.years).toEqual([2024, 2025]);
    expect(meta.departments).toContain("LIMA");

    const meta2024 = await (await request.get(`${base}/meta?year=2024`)).json();
    expect(meta2024.years).toEqual([2024, 2025]);
    expect(meta2024.departments).toEqual(["LIMA"]);
    expect(meta2024.categories).toEqual(["goods"]);
    expect(meta2024.amount_min).toBe(10000);
    expect(meta2024.amount_max).toBe(10000);

    const allStats = await (await request.get(`${base}/stats`)).json();
    expect(allStats).toMatchObject({ year: null, total: 37, mype_opportunities: 8 });

    const stats2024 = await (await request.get(`${base}/stats?year=2024`)).json();
    expect(stats2024).toMatchObject({ year: 2024, total: 1, mype_opportunities: 1 });
    expect(stats2024.by_department).toEqual([{ department: "LIMA", total: 1, mype: 1 }]);

    const stats2025 = await (await request.get(`${base}/stats?year=2025`)).json();
    expect(stats2025).toMatchObject({ year: 2025, total: 36, mype_opportunities: 7 });
    expect(stats2025.by_department).toContainEqual({ department: "LIMA", total: 30, mype: 3 });
    expect(stats2025.by_category).toContainEqual({ category: "goods", total: 4, mype: 3 });

    const all = await (await request.get(`${base}/opportunities?page_size=100`)).json();
    expect(all.total).toBe(37);

    const only2024 = await (await request.get(`${base}/opportunities?year=2024`)).json();
    expect(only2024.total).toBe(1);
    expect(only2024.items.map((item: { ocid: string }) => item.ocid)).toEqual(["ocds-test-0010"]);

    const only2025 = await (
      await request.get(`${base}/opportunities?year=2025&page_size=100`)
    ).json();
    expect(only2025.total).toBe(36);
    expect(
      only2025.items.every(
        (item: { segmentation_year: number }) => item.segmentation_year === 2025,
      ),
    ).toBe(true);
  });
});
