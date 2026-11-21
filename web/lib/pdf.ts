import { PDFDocument, PDFFont, PDFPage, StandardFonts, rgb } from "pdf-lib";
import { formatDate, formatPEN } from "./format";
import type { Checklist } from "./types";

const PAGE_WIDTH = 595.28;
const PAGE_HEIGHT = 841.89;
const MARGIN = 48;
const BOTTOM = 58;
const CONTENT_WIDTH = PAGE_WIDTH - MARGIN * 2;

const NAVY = rgb(0.043, 0.145, 0.27);
const TEAL = rgb(0.05, 0.47, 0.44);
const INK = rgb(0.1, 0.1, 0.1);
const MUTED = rgb(0.4, 0.4, 0.4);
const AMBER = rgb(0.48, 0.28, 0.02);
const WHITE = rgb(1, 1, 1);
const RULE = rgb(0.85, 0.85, 0.83);

const REPLACEMENTS: Array<[RegExp, string]> = [
  [/\u2018|\u2019/g, "'"],
  [/\u201c|\u201d/g, '"'],
  [/\u2013|\u2014/g, "-"],
  [/\u2022/g, "-"],
  [/\u2026/g, "..."],
  [/\u00a0/g, " "],
];

function safeText(value: string): string {
  let text = value.replace(/\r/g, "").replace(/\t/g, "  ");
  for (const [pattern, replacement] of REPLACEMENTS) {
    text = text.replace(pattern, replacement);
  }
  text = text.replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f-\u009f]/g, "");
  return Array.from(text)
    .map((character) => (character.codePointAt(0)! <= 0xff ? character : "?"))
    .join("");
}

function wrapText(text: string, font: PDFFont, size: number, width: number): string[] {
  const lines: string[] = [];
  for (const paragraph of safeText(text).split("\n")) {
    if (!paragraph.trim()) {
      lines.push("");
      continue;
    }
    let line = "";
    for (const word of paragraph.split(/\s+/)) {
      const candidate = line ? `${line} ${word}` : word;
      if (font.widthOfTextAtSize(candidate, size) <= width) {
        line = candidate;
        continue;
      }
      if (line) {
        lines.push(line);
        line = "";
      }
      if (font.widthOfTextAtSize(word, size) <= width) {
        line = word;
        continue;
      }
      let chunk = "";
      for (const character of word) {
        if (font.widthOfTextAtSize(chunk + character, size) > width) {
          if (chunk) lines.push(chunk);
          chunk = character;
        } else {
          chunk += character;
        }
      }
      line = chunk;
    }
    if (line) lines.push(line);
  }
  return lines.length ? lines : [""];
}

interface Writer {
  pages: PDFPage[];
  gap: (value: number) => void;
  paragraph: (
    text: string,
    options?: {
      font?: PDFFont;
      size?: number;
      color?: ReturnType<typeof rgb>;
      lineHeight?: number;
      width?: number;
    },
  ) => void;
  heading: (text: string) => void;
  ensure: (height: number) => void;
}

function createWriter(
  document: PDFDocument,
  regular: PDFFont,
  bold: PDFFont,
  firstPage: PDFPage,
  startY: number,
): Writer {
  const pages: PDFPage[] = [firstPage];
  let page = firstPage;
  let y = startY;

  const newPage = () => {
    page = document.addPage([PAGE_WIDTH, PAGE_HEIGHT]);
    pages.push(page);
    page.drawText(safeText("ContrataMYPE · Checklist (continuación)"), {
      x: MARGIN,
      y: PAGE_HEIGHT - 34,
      size: 8,
      font: regular,
      color: MUTED,
    });
    page.drawLine({
      start: { x: MARGIN, y: PAGE_HEIGHT - 42 },
      end: { x: PAGE_WIDTH - MARGIN, y: PAGE_HEIGHT - 42 },
      thickness: 0.5,
      color: RULE,
    });
    y = PAGE_HEIGHT - 58;
  };

  const ensure = (height: number) => {
    if (y - height < BOTTOM) newPage();
  };

  const gap = (value: number) => {
    y -= value;
  };

  const paragraph: Writer["paragraph"] = (text, options = {}) => {
    const font = options.font ?? regular;
    const size = options.size ?? 10;
    const lineHeight = options.lineHeight ?? size * 1.45;
    const color = options.color ?? INK;
    const width = options.width ?? CONTENT_WIDTH;
    for (const line of wrapText(text, font, size, width)) {
      ensure(lineHeight);
      if (line) {
        page.drawText(line, { x: MARGIN, y: y - size, size, font, color });
      }
      y -= lineHeight;
    }
  };

  const heading = (text: string) => {
    gap(10);
    ensure(30);
    page.drawText(safeText(text), {
      x: MARGIN,
      y: y - 14,
      size: 13,
      font: bold,
      color: NAVY,
    });
    y -= 21;
    page.drawRectangle({
      x: MARGIN,
      y: y + 3,
      width: 42,
      height: 2,
      color: TEAL,
    });
    gap(9);
  };

  return {
    pages,
    gap,
    paragraph,
    heading,
    ensure,
  };
}

export async function buildChecklistPdf(checklist: Checklist): Promise<Uint8Array> {
  const document = await PDFDocument.create();
  document.setTitle(`Checklist de participación · ${checklist.ocid}`);
  document.setSubject("Checklist generado a partir de campos oficiales OCDS");
  document.setAuthor("ContrataMYPE");
  document.setCreator("ContrataMYPE");
  document.setProducer("ContrataMYPE (pdf-lib)");

  const regular = await document.embedFont(StandardFonts.Helvetica);
  const bold = await document.embedFont(StandardFonts.HelveticaBold);
  const firstPage = document.addPage([PAGE_WIDTH, PAGE_HEIGHT]);

  firstPage.drawRectangle({
    x: 0,
    y: PAGE_HEIGHT - 96,
    width: PAGE_WIDTH,
    height: 96,
    color: NAVY,
  });
  firstPage.drawRectangle({
    x: 0,
    y: PAGE_HEIGHT - 99,
    width: PAGE_WIDTH,
    height: 3,
    color: TEAL,
  });
  firstPage.drawText("ContrataMYPE", {
    x: MARGIN,
    y: PAGE_HEIGHT - 42,
    size: 20,
    font: bold,
    color: WHITE,
  });
  firstPage.drawText("Checklist de participación", {
    x: MARGIN,
    y: PAGE_HEIGHT - 63,
    size: 11,
    font: regular,
    color: WHITE,
  });
  firstPage.drawText("Datos abiertos OECE · OCDS · CC BY 4.0", {
    x: MARGIN,
    y: PAGE_HEIGHT - 79,
    size: 8,
    font: regular,
    color: rgb(0.78, 0.85, 0.92),
  });

  const writer = createWriter(document, regular, bold, firstPage, PAGE_HEIGHT - 122);

  writer.paragraph(checklist.process.title?.trim() || "Proceso sin título", {
    font: bold,
    size: 16,
    lineHeight: 20,
  });
  writer.gap(2);
  writer.paragraph(`OCID: ${checklist.ocid}`, {
    size: 9,
    color: MUTED,
    lineHeight: 12,
  });
  writer.paragraph(
    checklist.process.mype_fit === true
      ? "Compatibilidad MYPE: compatible (heurística de compatibilidad MYPE, no elegibilidad legal)."
      : checklist.process.mype_fit === false
        ? "Compatibilidad MYPE: no compatible (heurística de compatibilidad MYPE, no elegibilidad legal)."
        : "Compatibilidad MYPE: sin clasificar en la base.",
    { size: 9, lineHeight: 12 },
  );

  writer.heading("Datos clave de la fuente");
  const amountText =
    checklist.process.amount_pen === null
      ? "No informado"
      : checklist.process.amount_pen === 0
        ? "S/ 0.00 (la fuente no informa un monto útil)"
        : formatPEN(checklist.process.amount_pen);
  const fields: Array<[string, string]> = [
    ["Entidad compradora", checklist.process.buyer_name ?? "No informada"],
    ["Departamento", checklist.process.department ?? "No informado"],
    ["Monto", amountText],
    ["Categoría", checklist.process.category ?? "No informada"],
    ["Método", checklist.process.method ?? "No informado"],
    ["Publicación", formatDate(checklist.process.published_date)],
    [
      "Período registrado",
      `${formatDate(checklist.process.tender_start)} a ${formatDate(checklist.process.tender_end)}`,
    ],
  ];
  for (const [label, value] of fields) {
    writer.paragraph(label.toUpperCase(), {
      size: 7.5,
      color: MUTED,
      lineHeight: 10,
    });
    writer.paragraph(value, { size: 10, lineHeight: 13 });
    writer.gap(3);
  }

  if (checklist.warnings.length > 0) {
    writer.heading("Datos incompletos en la fuente");
    for (const warning of checklist.warnings) {
      writer.paragraph(`- ${warning}`, {
        size: 9,
        color: AMBER,
        lineHeight: 12,
      });
    }
  }

  writer.heading("Pasos para revisar este proceso");
  checklist.items.forEach((item, index) => {
    writer.ensure(54);
    writer.paragraph(`${index + 1}. ${item.title}`, {
      font: bold,
      size: 11,
      lineHeight: 14,
    });
    writer.paragraph(item.detail, { size: 9, lineHeight: 12.5 });
    writer.paragraph(`Fuente: ${item.source}`, {
      size: 7.5,
      color: MUTED,
      lineHeight: 10,
    });
    writer.gap(6);
  });

  writer.heading("Fuente y límites");
  writer.paragraph(
    `${checklist.source.name} · ${checklist.source.license} · ${checklist.source.url}`,
    { size: 8.5, lineHeight: 11 },
  );
  writer.paragraph(checklist.disclaimer, {
    size: 9,
    color: AMBER,
    lineHeight: 12,
  });
  writer.paragraph(
    "Las bases del proceso y el cronograma publicado en el portal oficial prevalecen sobre este checklist.",
    { size: 8, color: MUTED, lineHeight: 11 },
  );

  const totalPages = writer.pages.length;
  writer.pages.forEach((page, index) => {
    page.drawLine({
      start: { x: MARGIN, y: 38 },
      end: { x: PAGE_WIDTH - MARGIN, y: 38 },
      thickness: 0.5,
      color: RULE,
    });
    page.drawText(
      safeText(`ContrataMYPE · ${checklist.ocid} · Página ${index + 1} de ${totalPages}`),
      {
        x: MARGIN,
        y: 25,
        size: 7,
        font: regular,
        color: MUTED,
      },
    );
  });

  return document.save();
}
