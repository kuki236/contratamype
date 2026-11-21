import { NextResponse } from "next/server";
import { ApiError, getChecklist } from "@/lib/api";
import { buildChecklistPdf } from "@/lib/pdf";

export const dynamic = "force-dynamic";

export async function GET(_request: Request, context: { params: Promise<{ ocid: string }> }) {
  const { ocid } = await context.params;
  let checklist;
  try {
    checklist = await getChecklist(ocid);
  } catch (error) {
    if (error instanceof ApiError && error.isJsonNotFound) {
      return new NextResponse("Checklist no encontrado.", {
        status: 404,
        headers: { "Content-Type": "text/plain; charset=utf-8" },
      });
    }
    return new NextResponse("No se pudo generar el PDF: la API no está disponible.", {
      status: 502,
      headers: { "Content-Type": "text/plain; charset=utf-8" },
    });
  }

  const pdf = await buildChecklistPdf(checklist);
  const filename = `checklist-${checklist.ocid.replace(/[^a-zA-Z0-9._-]+/g, "-")}.pdf`;

  return new NextResponse(Buffer.from(pdf), {
    status: 200,
    headers: {
      "Content-Type": "application/pdf",
      "Content-Disposition": `attachment; filename="${filename}"`,
      "Cache-Control": "no-store",
    },
  });
}
