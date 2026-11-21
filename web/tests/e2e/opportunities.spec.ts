import { expect, test } from "@playwright/test";

test.describe("búsqueda de oportunidades", () => {
  test("busca por texto y muestra la etiqueta MYPE", async ({ page }) => {
    await page.goto("/");

    await expect(
      page.getByRole("heading", { name: "Encuentra oportunidades para tu MYPE" }),
    ).toBeVisible();
    await expect(page.getByTestId("opportunity-card")).toHaveCount(7);
    await expect(page.getByText("Compra histórica fuera de la cohorte")).toHaveCount(0);

    const laptopCard = page
      .getByTestId("opportunity-card")
      .filter({ hasText: "Compra de laptops para capacitación" });
    await expect(laptopCard.getByTestId("mype-badge")).toHaveText("Compatible MYPE");

    await page.getByLabel("Buscar por texto").fill("laptops");
    await page.getByRole("button", { name: "Buscar oportunidades" }).click();

    await expect(page.getByTestId("opportunity-card")).toHaveCount(1);
    await expect(page.getByText("Compra de laptops para capacitación")).toBeVisible();
    await expect(page.getByText("Compra histórica fuera de la cohorte")).toHaveCount(0);
  });

  test("filtra por departamento, categoría y monto", async ({ page }) => {
    await page.goto("/");

    await page.getByLabel("Departamento").selectOption("CUSCO");
    await page.getByLabel("Compatibilidad MYPE").selectOption("0");
    await page.getByRole("button", { name: "Buscar oportunidades" }).click();

    await expect(page.getByTestId("opportunity-card")).toHaveCount(2);
    await expect(page.getByText("Servicio de limpieza de oficinas")).toBeVisible();
    await expect(page.getByText("Obra de saneamiento rural")).toBeVisible();
    await expect(page.getByText("Compra de laptops para capacitación")).toHaveCount(0);

    await page.goto("/?category=goods&mype_only=0");
    await expect(page.getByTestId("opportunity-card")).toHaveCount(4);
    await expect(page.getByText("Suministro de alimentos no perecibles")).toBeVisible();
    await expect(page.getByText("Servicio de limpieza de oficinas")).toHaveCount(0);

    await page.goto("/?min_amount=90000&max_amount=100000&mype_only=0");
    await expect(page.getByTestId("opportunity-card")).toHaveCount(1);
    await expect(page.getByText("Consultoría para expediente técnico")).toBeVisible();
  });

  test("muestra un estado vacío útil", async ({ page }) => {
    await page.goto("/?q=zzzz-no-existe");

    await expect(page.getByRole("heading", { name: "No encontramos oportunidades" })).toBeVisible();
    await expect(page.getByTestId("opportunity-card")).toHaveCount(0);
    await expect(
      page.getByTestId("empty-state").getByRole("link", { name: "Limpiar filtros" }),
    ).toBeVisible();
  });
});

test.describe("detalle de oportunidad", () => {
  test("explica datos incompletos sin romper la ficha", async ({ page }) => {
    await page.goto("/opportunities/ocds-test-0002");

    await expect(
      page.getByRole("heading", { name: "Servicio de limpieza de oficinas" }),
    ).toBeVisible();
    await expect(page.getByText("La fuente no incluye una descripción del objeto.")).toBeVisible();
    await expect(
      page.getByText("La fuente registra la misma fecha de inicio y fin.", { exact: false }),
    ).toBeVisible();
    await expect(
      page.getByText("La fuente no reporta adjudicaciones para este proceso."),
    ).toBeVisible();
    await expect(page.getByTestId("mype-badge")).toHaveText("Compatible MYPE");

    await page.goto("/opportunities/ocds-test-0003");
    await expect(
      page.getByText("La fuente registra S/ 0.00 como monto (no informado útil)."),
    ).toBeVisible();
    await expect(page.getByText("Adjudicación sin proveedor identificado.").first()).toBeVisible();
    await expect(page.getByTestId("mype-badge")).toHaveText("No marcada compatible");

    await page.goto("/opportunities/ocds-test-0004");
    await expect(page.getByText("Contrato sin adjudicación vinculada.").first()).toBeVisible();
    await expect(page.getByText("Consultores del Sur EIRL").first()).toBeVisible();
  });

  test("muestra departamento desconocido y entidad ausente", async ({ page }) => {
    await page.goto("/opportunities/ocds-test-0005");

    await expect(
      page.getByRole("heading", { name: "Adquisición de mobiliario escolar" }),
    ).toBeVisible();
    await expect(page.getByText("DESCONOCIDO").first()).toBeVisible();
    await expect(page.getByText("Entidad compradora no informada.")).toBeVisible();
  });

  test("devuelve 404 para un OCID inexistente", async ({ page }) => {
    const response = await page.goto("/opportunities/ocds-test-9999");

    expect(response?.status()).toBe(404);
    await expect(page.getByRole("heading", { name: "Página no encontrada" })).toBeVisible();
  });
});

test.describe("checklist y PDF", () => {
  test("renderiza el checklist con cita y disclaimer", async ({ page }) => {
    await page.goto("/opportunities/ocds-test-0001/checklist");

    await expect(page.getByRole("heading", { name: "Checklist de participación" })).toBeVisible();
    await expect(page.getByText("ocds-test-0001").first()).toBeVisible();
    await expect(page.getByText("OECE", { exact: false }).first()).toBeVisible();
    await expect(page.getByTestId("disclaimer")).toContainText(
      "heurística de compatibilidad MYPE, no elegibilidad legal",
    );
    await expect(page.getByRole("button", { name: "Imprimir" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Descargar PDF" })).toHaveAttribute(
      "href",
      "/opportunities/ocds-test-0001/checklist/pdf",
    );

    await page.goto("/opportunities/ocds-test-0002/checklist");
    const warnings = page.getByTestId("checklist-warnings");
    await expect(
      warnings.getByText("La fuente no incluye una descripción del objeto."),
    ).toBeVisible();
    await expect(
      warnings.getByText("La fuente registra la misma fecha de inicio y fin.", { exact: false }),
    ).toBeVisible();
  });

  test("descarga un PDF real", async ({ request }) => {
    const response = await request.get("/opportunities/ocds-test-0001/checklist/pdf");

    expect(response.status()).toBe(200);
    expect(response.headers()["content-type"]).toContain("application/pdf");
    expect(response.headers()["content-disposition"]).toContain("attachment");
    const body = await response.body();
    expect(body.subarray(0, 4).toString()).toBe("%PDF");
    expect(body.length).toBeGreaterThan(1000);
  });
});
