/**
 * Builds the ContrataMYPE PBIR pages and visuals.
 *
 * The semantic model is TMDL; this script only writes report-side JSON.
 * Run `node dashboard/build_report.mjs` after changing the layout, then
 * `powerbi-report-author validate dashboard/ContrataMYPE.Report`.
 */

import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";

const ROOT = path.resolve("dashboard/ContrataMYPE.Report/definition");
const P1 = "4d2a7c1e9b8f4a6d3c05";
const P2 = "8f6b3e1d5a9c4e7b2d06";

const SCHEMA_VISUAL =
  "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.9.0/schema.json";
const SCHEMA_PAGE =
  "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json";
const SCHEMA_PAGES =
  "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json";

const C = {
  canvas: "#F8FAFC",
  white: "#FFFFFF",
  navy: "#0F172A",
  blue: "#1D4ED8",
  blueDark: "#1E3A8A",
  teal: "#0F766E",
  tealDark: "#115E59",
  amber: "#B45309",
  gray: "#94A3B8",
  grayLight: "#E2E8F0",
  inkSecondary: "#475569",
  inkTertiary: "#64748B",
  border: "#E2E8F0",
  rowAlt: "#F8FAFC",
  headerBg: "#F1F5F9",
};

const lit = (value) => ({ expr: { Literal: { Value: value } } });
const raw = (value) => ({ Literal: { Value: value } });
const str = (value) => lit(`'${String(value).replaceAll("'", "''")}'`);
const num = (value) => lit(`${value}D`);
const int = (value) => lit(`${value}L`);
const bool = (value) => lit(value ? "true" : "false");
const solid = (hex) => ({ solid: { color: str(hex) } });

const column = (entity, property) => ({
  Column: { Expression: { SourceRef: { Entity: entity } }, Property: property },
});
const measure = (entity, property) => ({
  Measure: { Expression: { SourceRef: { Entity: entity } }, Property: property },
});
const projection = (field, queryRef, nativeQueryRef) => ({ field, queryRef, nativeQueryRef });

const visualName = (key) => crypto.createHash("sha256").update(key).digest("hex").slice(0, 20);
const filterName = (key) => `Filter${crypto.createHash("sha256").update(key).digest("hex").slice(0, 24)}`;

const background = (show, hex = C.white) => [
  { properties: { show: bool(show), color: solid(hex), transparency: num(0) } },
];
const border = (show, hex = C.border) => [
  { properties: { show: bool(show), color: solid(hex), radius: num(8), width: num(1) } },
];
const padding = (top, bottom, left, right) => [
  { properties: { top: num(top), bottom: num(bottom), left: num(left), right: num(right) } },
];
const visualHeader = (show = false) => [{ properties: { show: bool(show) } }];
const titleVco = (text, size = 13) => [
  {
    properties: {
      show: bool(true),
      text: str(text),
      fontSize: num(size),
      fontColor: solid(C.navy),
      bold: bool(true),
      alignment: str("left"),
    },
  },
];
const subtitleVco = (text) => [
  {
    properties: {
      show: bool(true),
      text: str(text),
      fontSize: num(9),
      fontColor: solid(C.inkSecondary),
      alignment: str("left"),
    },
  },
];
const altText = (text) => [{ properties: { altText: str(text) } }];

function paragraph(text, sizePx, hex, options = {}) {
  return {
    textRuns: [
      {
        value: text,
        textStyle: {
          fontFamily: options.family ?? "Segoe UI",
          fontSize: `${sizePx}px`,
          color: hex,
          ...(options.bold ? { fontWeight: "bold" } : {}),
        },
      },
    ],
    horizontalTextAlignment: options.align ?? "left",
  };
}

function writeVisual(pageId, visual) {
  const directory = path.join(ROOT, "pages", pageId, "visuals", visual.name);
  fs.mkdirSync(directory, { recursive: true });
  fs.writeFileSync(path.join(directory, "visual.json"), `${JSON.stringify(visual, null, 2)}\n`, "utf8");
}

function textbox({ key, x, y, width, height, paragraphs, alt = null }) {
  return {
    $schema: SCHEMA_VISUAL,
    name: visualName(`textbox:${key}`),
    position: { x, y, z: 1000, height, width, tabOrder: 1000 },
    visual: {
      visualType: "textbox",
      objects: { general: [{ properties: { paragraphs } }] },
      visualContainerObjects: {
        background: background(false),
        border: border(false),
        padding: padding(0, 0, 0, 0),
        ...(alt ? { general: altText(alt) } : {}),
      },
    },
  };
}

function navButton({ key, x, y, width, height, label, targetPageId, tooltip, icon, iconPlacement, alt }) {
  const textProperties = {
    text: str(label),
    fontSize: num(11),
    fontColor: solid(C.white),
    bold: bool(true),
    horizontalAlignment: str("center"),
  };
  if (iconPlacement === "right") {
    textProperties.leftMargin = int(12);
    textProperties.rightMargin = int(28);
  } else {
    textProperties.leftMargin = int(28);
    textProperties.rightMargin = int(12);
  }

  return {
    $schema: SCHEMA_VISUAL,
    name: visualName(`nav:${key}`),
    position: { x, y, z: 1000, height, width, tabOrder: 1000 },
    visual: {
      visualType: "actionButton",
      objects: {
        text: [{ properties: { show: bool(true) } }, { properties: textProperties, selector: { id: "default" } }],
        icon: [
          { properties: { show: bool(true) } },
          {
            properties: {
              shapeType: str(icon),
              placement: str(iconPlacement),
              lineColor: solid(C.white),
              lineWeight: int(2),
              iconSize: num(14),
            },
            selector: { id: "default" },
          },
        ],
        fill: [
          { properties: { show: bool(true) } },
          { properties: { fillColor: solid(C.blue) }, selector: { id: "default" } },
          { properties: { fillColor: solid(C.blueDark) }, selector: { id: "hover" } },
        ],
        outline: [{ properties: { show: bool(false) } }],
        shape: [
          { properties: { tileShape: str("rectangleRounded"), roundEdge: int(8) } },
          { properties: { tileShape: str("rectangleRounded") }, selector: { id: "default" } },
        ],
      },
      visualContainerObjects: {
        background: background(false),
        border: border(false),
        padding: padding(0, 0, 0, 0),
        visualHeader: visualHeader(false),
        visualLink: [
          {
            properties: {
              show: bool(true),
              type: str("PageNavigation"),
              navigationSection: str(targetPageId),
              tooltip: str(tooltip),
            },
          },
        ],
        general: altText(alt),
      },
    },
    howCreated: "InsertVisualButton",
  };
}

function cardVisual({
  key,
  x,
  y,
  width,
  height,
  measureName,
  label,
  valueHex,
  accentHex,
  alt,
  displayUnits = null,
  precision = 0,
}) {
  const valueProperties = {
    fontSize: num(26),
    fontColor: solid(valueHex),
    bold: bool(true),
  };
  if (displayUnits) {
    valueProperties.labelDisplayUnits = str(displayUnits);
    valueProperties.labelPrecision = int(precision);
  }

  return {
    $schema: SCHEMA_VISUAL,
    name: visualName(`card:${key}`),
    position: { x, y, z: 1000, height, width, tabOrder: 1000 },
    visual: {
      visualType: "cardVisual",
      query: {
        queryState: {
          Data: {
            projections: [projection(measure("Tenders", measureName), `Tenders.${measureName}`, measureName)],
          },
        },
      },
      objects: {
        value: [{ properties: valueProperties, selector: { id: "default" } }],
        label: [
          {
            properties: {
              show: bool(true),
              text: str(label),
              fontSize: num(11),
              fontColor: solid(C.inkSecondary),
            },
            selector: { id: "default" },
          },
        ],
        padding: [{ properties: { paddingUniform: num(10) }, selector: { id: "default" } }],
        layout: [{ properties: { paddingUniform: num(0) }, selector: { id: "default" } }],
        accentBar: [
          {
            properties: {
              show: bool(true),
              position: str("Left"),
              color: solid(accentHex),
              width: num(4),
            },
            selector: { id: "default" },
          },
        ],
      },
      visualContainerObjects: {
        background: background(true),
        border: border(true),
        padding: padding(8, 8, 8, 8),
        visualHeader: visualHeader(false),
        title: [{ properties: { show: bool(false) } }],
        general: altText(alt),
      },
    },
  };
}

function categoricalFilter({ key, entity, property, values, scope = "page" }) {
  const literals = values.map((value) => {
    if (typeof value === "number") {
      return [raw(Number.isInteger(value) ? `${value}L` : `${value}D`)];
    }
    if (typeof value === "boolean") {
      return [raw(value ? "true" : "false")];
    }
    return [raw(`'${String(value).replaceAll("'", "''")}'`)];
  });

  return {
    name: filterName(`${scope}:${key}`),
    field: column(entity, property),
    type: "Categorical",
    filter: {
      Version: 2,
      From: [{ Name: "c", Entity: entity, Type: 0 }],
      Where: [
        {
          Condition: {
            In: {
              Expressions: [
                { Column: { Expression: { SourceRef: { Source: "c" } }, Property: property } },
              ],
              Values: literals,
            },
          },
        },
      ],
    },
    howCreated: "User",
  };
}

function topNFilter({ key, entity, fieldProperty, orderProperty, top, direction }) {
  return {
    name: filterName(`topn:${key}`),
    field: column(entity, fieldProperty),
    type: "TopN",
    filter: {
      Version: 2,
      From: [
        {
          Name: "subquery",
          Expression: {
            Subquery: {
              Query: {
                Version: 2,
                From: [{ Name: "c", Entity: entity, Type: 0 }],
                Select: [
                  {
                    Column: { Expression: { SourceRef: { Source: "c" } }, Property: fieldProperty },
                    Name: "field",
                  },
                ],
                OrderBy: [
                  {
                    Direction: direction,
                    Expression: {
                      Aggregation: {
                        Expression: {
                          Column: {
                            Expression: { SourceRef: { Source: "c" } },
                            Property: orderProperty,
                          },
                        },
                        Function: 0,
                      },
                    },
                  },
                  {
                    Direction: 1,
                    Expression: {
                      Column: {
                        Expression: { SourceRef: { Source: "c" } },
                        Property: fieldProperty,
                      },
                    },
                  },
                ],
                Top: top,
              },
            },
          },
          Type: 2,
        },
        { Name: "outer", Entity: entity, Type: 0 },
      ],
      Where: [
        {
          Condition: {
            In: {
              Expressions: [
                {
                  Column: {
                    Expression: { SourceRef: { Source: "outer" } },
                    Property: fieldProperty,
                  },
                },
              ],
              Table: { SourceRef: { Source: "subquery" } },
            },
          },
        },
      ],
    },
    howCreated: "User",
  };
}

function barChart({
  key,
  x,
  y,
  width,
  height,
  title,
  subtitle,
  categoryProperty,
  measureName,
  native,
  alt,
  topN = null,
  displayUnits = null,
  precision = 0,
  categoryFontSize = 9,
  labelFontSize = 10,
  innerPadding = 20,
  maxMargin = 45,
  fill = C.blue,
}) {
  const visual = {
    $schema: SCHEMA_VISUAL,
    name: visualName(`bar:${key}`),
    position: { x, y, z: 1000, height, width, tabOrder: 1000 },
    visual: {
      visualType: "barChart",
      query: {
        queryState: {
          Category: {
            projections: [projection(column("Tenders", categoryProperty), `Tenders.${categoryProperty}`, categoryProperty)],
          },
          Y: {
            projections: [projection(measure("Tenders", measureName), `Tenders.${measureName}`, native)],
          },
        },
        sortDefinition: {
          sort: [{ field: measure("Tenders", measureName), direction: "Descending" }],
          isDefaultSort: false,
        },
      },
      objects: {
        labels: [
          {
            properties: {
              show: bool(true),
              fontSize: num(labelFontSize),
              bold: bool(false),
              color: solid(C.navy),
              labelPosition: str("OutsideEnd"),
              ...(displayUnits
                ? { labelDisplayUnits: str(displayUnits), labelPrecision: int(precision) }
                : {}),
            },
          },
        ],
        valueAxis: [
          { properties: { show: bool(false), gridlineShow: bool(false), showAxisTitle: bool(false) } },
        ],
        categoryAxis: [
          {
            properties: {
              show: bool(true),
              fontSize: num(categoryFontSize),
              labelColor: solid(C.inkSecondary),
              showAxisTitle: bool(false),
              gridlineShow: bool(false),
              maxMarginFactor: int(maxMargin),
              innerPadding: int(innerPadding),
            },
          },
        ],
        legend: [{ properties: { show: bool(false) } }],
        dataPoint: [{ properties: { fill: solid(fill), borderShow: bool(false) } }],
      },
      visualContainerObjects: {
        background: background(true),
        border: border(true),
        padding: padding(8, 8, 8, 8),
        visualHeader: visualHeader(false),
        title: titleVco(title, 13),
        subTitle: subtitleVco(subtitle),
        general: altText(alt),
      },
    },
  };

  if (topN) {
    visual.filterConfig = {
      filters: [
        topNFilter({
          key,
          entity: "Tenders",
          fieldProperty: categoryProperty,
          orderProperty: topN.orderProperty,
          top: topN.top,
          direction: 2,
        }),
      ],
    };
  }

  return visual;
}

function bandBarChart({
  key,
  x,
  y,
  width,
  height,
  title,
  subtitle,
  alt,
}) {
  return {
    $schema: SCHEMA_VISUAL,
    name: visualName(`bandbar:${key}`),
    position: { x, y, z: 1000, height, width, tabOrder: 1000 },
    visual: {
      visualType: "barChart",
      query: {
        queryState: {
          Category: {
            projections: [
              projection(column("Tenders", "Rango de monto"), "Tenders.Rango de monto", "Rango de monto"),
            ],
          },
          Y: {
            projections: [projection(measure("Tenders", "Procesos"), "Tenders.Procesos", "Procesos")],
          },
        },
        sortDefinition: {
          sort: [{ field: column("Tenders", "amount_band_order"), direction: "Ascending" }],
          isDefaultSort: false,
        },
      },
      objects: {
        labels: [
          {
            properties: {
              show: bool(true),
              fontSize: num(10),
              color: solid(C.navy),
              labelPosition: str("OutsideEnd"),
              labelDisplayUnits: str("1"),
              labelPrecision: int(0),
            },
          },
        ],
        valueAxis: [
          { properties: { show: bool(false), gridlineShow: bool(false), showAxisTitle: bool(false) } },
        ],
        categoryAxis: [
          {
            properties: {
              show: bool(true),
              fontSize: num(9),
              labelColor: solid(C.inkSecondary),
              showAxisTitle: bool(false),
              gridlineShow: bool(false),
              maxMarginFactor: int(45),
              innerPadding: int(20),
            },
          },
        ],
        legend: [{ properties: { show: bool(false) } }],
        dataPoint: [
          { properties: { fill: solid(C.blue), borderShow: bool(false) } },
          {
            properties: { fill: solid(C.gray) },
            selector: {
              data: [
                {
                  scopeId: {
                    Comparison: {
                      ComparisonKind: 0,
                      Left: column("Tenders", "Rango de monto"),
                      Right: raw("'Sin monto'"),
                    },
                  },
                },
              ],
            },
          },
        ],
      },
      visualContainerObjects: {
        background: background(true),
        border: border(true),
        padding: padding(8, 8, 8, 8),
        visualHeader: visualHeader(false),
        title: titleVco(title, 13),
        subTitle: subtitleVco(subtitle),
        general: altText(alt),
      },
    },
  };
}

function lineChart({
  key,
  x,
  y,
  width,
  height,
  title,
  subtitle,
  alt,
}) {
  const visual = {
    $schema: SCHEMA_VISUAL,
    name: visualName(`line:${key}`),
    position: { x, y, z: 1000, height, width, tabOrder: 1000 },
    visual: {
      visualType: "lineChart",
      query: {
        queryState: {
          Category: {
            projections: [projection(column("Tenders", "Mes"), "Tenders.Mes", "Mes")],
          },
          Series: {
            projections: [
              projection(
                column("Tenders", "Año de cohorte"),
                "Tenders.Año de cohorte",
                "Año de cohorte",
              ),
            ],
          },
          Y: {
            projections: [projection(measure("Tenders", "Procesos"), "Tenders.Procesos", "Procesos")],
          },
        },
        sortDefinition: {
          sort: [{ field: column("Tenders", "month_order"), direction: "Ascending" }],
          isDefaultSort: false,
        },
      },
      objects: {
        labels: [{ properties: { show: bool(false) } }],
        valueAxis: [
          {
            properties: {
              show: bool(true),
              gridlineShow: bool(true),
              gridlineColor: solid(C.grayLight),
              fontSize: num(9),
              labelColor: solid(C.inkTertiary),
              showAxisTitle: bool(false),
            },
          },
        ],
        categoryAxis: [
          {
            properties: {
              show: bool(true),
              fontSize: num(9),
              labelColor: solid(C.inkSecondary),
              showAxisTitle: bool(false),
              gridlineShow: bool(false),
            },
          },
        ],
        lineStyles: [
          {
            properties: {
              strokeWidth: num(2.5),
              showMarker: bool(true),
              markerSize: num(5),
            },
          },
        ],
        legend: [
          {
            properties: {
              show: bool(true),
              position: str("Bottom"),
              fontSize: num(9),
              labelColor: solid(C.inkSecondary),
            },
          },
        ],
      },
      visualContainerObjects: {
        background: background(true),
        border: border(true),
        padding: padding(8, 8, 8, 8),
        visualHeader: visualHeader(false),
        title: titleVco(title, 13),
        subTitle: subtitleVco(subtitle),
        general: altText(alt),
      },
    },
  };

  return visual;
}

function donutChart({ key, x, y, width, height, title, subtitle, alt }) {
  return {
    $schema: SCHEMA_VISUAL,
    name: visualName(`donut:${key}`),
    position: { x, y, z: 1000, height, width, tabOrder: 1000 },
    visual: {
      visualType: "donutChart",
      query: {
        queryState: {
          Category: {
            projections: [
              projection(
                column("Tenders", "Compatibilidad MYPE"),
                "Tenders.Compatibilidad MYPE",
                "Compatibilidad MYPE",
              ),
            ],
          },
          Y: {
            projections: [projection(measure("Tenders", "Monto total"), "Tenders.Monto total", "Monto total")],
          },
        },
      },
      objects: {
        labels: [
          {
            properties: {
              show: bool(true),
              fontSize: num(9),
              color: solid(C.navy),
              labelStyle: str("Category, percent of total"),
              percentageLabelPrecision: int(1),
              position: str("outside"),
            },
          },
        ],
        legend: [{ properties: { show: bool(false) } }],
        dataPoint: [
          { properties: { fill: solid(C.gray), borderShow: bool(false) } },
          {
            properties: { fill: solid(C.teal) },
            selector: {
              data: [
                {
                  scopeId: {
                    Comparison: {
                      ComparisonKind: 0,
                      Left: column("Tenders", "Compatibilidad MYPE"),
                      Right: raw("'Compatible MYPE'"),
                    },
                  },
                },
              ],
            },
          },
          {
            properties: { fill: solid(C.gray) },
            selector: {
              data: [
                {
                  scopeId: {
                    Comparison: {
                      ComparisonKind: 0,
                      Left: column("Tenders", "Compatibilidad MYPE"),
                      Right: raw("'No compatible'"),
                    },
                  },
                },
              ],
            },
          },
        ],
      },
      visualContainerObjects: {
        background: background(true),
        border: border(true),
        padding: padding(8, 8, 8, 8),
        visualHeader: visualHeader(false),
        title: titleVco(title, 13),
        subTitle: subtitleVco(subtitle),
        general: altText(alt),
      },
    },
  };
}

function tableVisual({
  key,
  x,
  y,
  width,
  height,
  title,
  subtitle,
  values,
  widths,
  sortBy,
  sortDirection = "Descending",
  alt,
  fontSize = 9,
  titleSize = 13,
  outerPadding = 12,
  columnAlignments = [],
}) {
  const visual = {
    visualType: "tableEx",
    query: {
      queryState: {
        Values: {
          projections: values.map((value) => projection(value.field, value.queryRef, value.native)),
        },
      },
    },
    objects: {
      columnHeaders: [
        {
          properties: {
            autoSizeColumnWidth: bool(!widths),
            columnAdjustment: str(widths ? "fixedWidth" : "growToFit"),
            customColumnWidth: bool(Boolean(widths)),
            backColor: solid(C.headerBg),
            fontColor: solid(C.navy),
            fontSize: num(fontSize),
            bold: bool(true),
            alignment: str("Auto"),
          },
        },
      ],
      values: [
        {
          properties: {
            backColorPrimary: solid(C.white),
            backColorSecondary: solid(C.rowAlt),
            fontColorPrimary: solid(C.navy),
            fontColorSecondary: solid(C.navy),
            fontSize: num(fontSize),
            wordWrap: bool(false),
          },
        },
      ],
      grid: [
        {
          properties: {
            gridHorizontal: bool(true),
            gridHorizontalColor: solid(C.border),
            gridHorizontalWeight: num(1),
            gridVertical: bool(false),
            rowPadding: num(3),
          },
        },
      ],
      total: [{ properties: { totals: bool(false) } }],
    },
    visualContainerObjects: {
      background: background(true),
      border: border(true),
      padding: padding(outerPadding, outerPadding, outerPadding, outerPadding),
      visualHeader: visualHeader(false),
      title: titleVco(title, titleSize),
      subTitle: subtitleVco(subtitle),
      stylePreset: [{ properties: { name: str("None") } }],
      general: altText(alt),
    },
  };

  if (widths) {
    visual.objects.columnWidth = widths.map(({ queryRef, width: columnWidth }) => ({
      properties: { value: num(columnWidth) },
      selector: { metadata: queryRef },
    }));
  }
  if (columnAlignments.length) {
    visual.objects.columnFormatting = columnAlignments.map(({ queryRef, alignment }) => ({
      properties: { alignment: str(alignment), styleHeader: bool(true), styleValues: bool(true) },
      selector: { metadata: queryRef },
    }));
  }
  if (sortBy) {
    visual.query.sortDefinition = {
      sort: [{ field: sortBy, direction: sortDirection }],
      isDefaultSort: false,
    };
  }

  return {
    $schema: SCHEMA_VISUAL,
    name: visualName(`table:${key}`),
    position: { x, y, z: 1000, height, width, tabOrder: 1000 },
    visual,
  };
}

function slicerVisual({ key, x, y, width, height, property, header, alt }) {
  return {
    $schema: SCHEMA_VISUAL,
    name: visualName(`slicer:${key}`),
    position: { x, y, z: 1000, height, width, tabOrder: 1000 },
    visual: {
      visualType: "slicer",
      query: {
        queryState: {
          Values: {
            projections: [projection(column("Tenders", property), `Tenders.${property}`, property)],
          },
        },
      },
      objects: {
        data: [{ properties: { mode: str("Dropdown") } }],
        header: [
          {
            properties: {
              show: bool(true),
              text: str(header),
              showRestatement: bool(false),
            },
          },
        ],
      },
      visualContainerObjects: {
        background: background(true),
        border: border(true),
        padding: padding(8, 8, 8, 8),
        visualHeader: visualHeader(false),
        general: altText(alt),
      },
    },
  };
}

function writePage(pageId, displayName, filters) {
  const directory = path.join(ROOT, "pages", pageId);
  fs.mkdirSync(path.join(directory, "visuals"), { recursive: true });
  const page = {
    $schema: SCHEMA_PAGE,
    name: pageId,
    displayName,
    displayOption: "FitToPage",
    height: 1080,
    width: 1920,
    filterConfig: { filters },
    objects: {
      background: [{ properties: { color: solid(C.canvas), transparency: num(0) } }],
      outspace: [{ properties: { color: solid(C.canvas), transparency: num(0) } }],
    },
  };
  fs.writeFileSync(path.join(directory, "page.json"), `${JSON.stringify(page, null, 2)}\n`, "utf8");
}

// ---------------------------------------------------------------------------
// Page 1 — Mercado
// ---------------------------------------------------------------------------

fs.rmSync(path.join(ROOT, "pages"), { recursive: true, force: true });

writePage(P1, "Mercado", [
  categoricalFilter({
    key: "page1-cohort",
    entity: "Tenders",
    property: "Año de cohorte",
    values: [2024, 2025],
  }),
]);

const p1Visuals = [];

p1Visuals.push(
  textbox({
    key: "p1-title",
    x: 32,
    y: 24,
    width: 900,
    height: 64,
    paragraphs: [paragraph("El mercado de compras públicas 2024–2025", 32, C.navy, { family: "Segoe UI Semibold", bold: true })],
  }),
);

p1Visuals.push(
  textbox({
    key: "p1-source",
    x: 948,
    y: 24,
    width: 400,
    height: 64,
    paragraphs: [
      paragraph("Fuente: OECE — Contrataciones Abiertas (OCDS) · CC BY 4.0", 10, C.inkSecondary, { align: "right" }),
      paragraph("Cohortes 2024–2025 · montos en S/", 10, C.inkSecondary, { align: "right" }),
    ],
  }),
);

p1Visuals.push(
  slicerVisual({
    key: "p1-year",
    x: 1364,
    y: 24,
    width: 176,
    height: 80,
    property: "Año de cohorte",
    header: "Año de cohorte",
    alt: "Selector para filtrar ambas páginas por cohorte: todos, 2024 o 2025.",
  }),
);

p1Visuals.push(
  navButton({
    key: "p1-nav",
    x: 1556,
    y: 32,
    width: 332,
    height: 48,
    label: "Explorar oportunidades",
    targetPageId: P2,
    tooltip: "Abrir el explorador de oportunidades MYPE",
    icon: "rightArrow",
    iconPlacement: "right",
    alt: "Botón para abrir el explorador de oportunidades MYPE",
  }),
);

const kpis = [
  { key: "procesos", measure: "Procesos", label: "Procesos en la cohorte", color: C.navy, accent: C.blue, displayUnits: "1", precision: 0, alt: "Tarjeta con la cantidad de procesos de las cohortes 2024–2025." },
  { key: "monto", measure: "Monto total", label: "Monto convocado", color: C.navy, accent: C.blue, displayUnits: "1000000", precision: 0, alt: "Tarjeta con el monto total convocado, en millones de soles." },
  { key: "mediano", measure: "Monto mediano", label: "Monto mediano", color: C.navy, accent: C.blue, displayUnits: "1000", precision: 1, alt: "Tarjeta con la mediana del monto referencial, en miles de soles." },
  { key: "mype", measure: "Oportunidades MYPE", label: "Oportunidades MYPE", color: C.teal, accent: C.teal, displayUnits: "1", precision: 0, alt: "Tarjeta con la cantidad de procesos compatibles con la heurística MYPE." },
  { key: "pct-mype", measure: "% MYPE", label: "% MYPE de los procesos", color: C.amber, accent: C.amber, alt: "Tarjeta con el porcentaje de procesos compatibles MYPE." },
  { key: "ticket", measure: "Ticket promedio", label: "Ticket promedio", color: C.inkSecondary, accent: C.inkTertiary, displayUnits: "1000", precision: 0, alt: "Tarjeta con el monto promedio por proceso, en miles de soles." },
];

kpis.forEach((kpi, index) => {
  p1Visuals.push(
    cardVisual({
      key: `p1-${kpi.key}`,
      x: 32 + index * 312,
      y: 112,
      width: 296,
      height: 96,
      measureName: kpi.measure,
      label: kpi.label,
      valueHex: kpi.color,
      accentHex: kpi.accent,
      alt: kpi.alt,
      displayUnits: kpi.displayUnits ?? null,
      precision: kpi.precision ?? 0,
    }),
  );
});

p1Visuals.push(
  barChart({
    key: "p1-departments",
    x: 32,
    y: 232,
    width: 1088,
    height: 344,
    title: "Monto convocado por departamento",
    subtitle: "Top 10 por monto referencial; miles de millones de S/",
    categoryProperty: "Departamento",
    measureName: "Monto (miles de millones S/)",
    native: "Monto (miles de millones S/)",
    alt: "Barras horizontales con los 10 departamentos de mayor monto convocado en la cohorte 2025.",
    topN: { orderProperty: "Monto (S/)", top: 10 },
    displayUnits: null,
    precision: 0,
    categoryFontSize: 9,
    labelFontSize: 10,
    innerPadding: 16,
    maxMargin: 45,
  }),
);

p1Visuals.push(
  tableVisual({
    key: "p1-categories",
    x: 1144,
    y: 232,
    width: 744,
    height: 344,
    title: "Procesos y monto por categoría",
    subtitle: "Participación MYPE dentro de cada categoría OCDS",
    values: [
      { field: column("Tenders", "Categoría"), queryRef: "Tenders.Categoría", native: "Categoría" },
      { field: measure("Tenders", "Procesos"), queryRef: "Tenders.Procesos", native: "Procesos" },
      { field: measure("Tenders", "Monto total"), queryRef: "Tenders.Monto total", native: "Monto total" },
      { field: measure("Tenders", "% MYPE"), queryRef: "Tenders.% MYPE", native: "% MYPE" },
    ],
    widths: [
      { queryRef: "Tenders.Categoría", width: 160 },
      { queryRef: "Tenders.Procesos", width: 110 },
      { queryRef: "Tenders.Monto total", width: 220 },
      { queryRef: "Tenders.% MYPE", width: 110 },
    ],
    sortBy: measure("Tenders", "Monto total"),
    sortDirection: "Descending",
    alt: "Tabla con procesos, monto convocado y porcentaje MYPE para bienes, servicios y obras.",
    fontSize: 10,
    titleSize: 13,
    outerPadding: 12,
    columnAlignments: [
      { queryRef: "Tenders.Procesos", alignment: "Right" },
      { queryRef: "Tenders.Monto total", alignment: "Right" },
      { queryRef: "Tenders.% MYPE", alignment: "Right" },
    ],
  }),
);

p1Visuals.push(
  lineChart({
    key: "p1-monthly",
    x: 32,
    y: 600,
    width: 752,
    height: 400,
    title: "Evolución mensual por cohorte",
    subtitle: "Procesos por mes de publicación; cohortes 2024–2025",
    alt: "Línea mensual de procesos publicados, comparando las cohortes 2024 y 2025.",
  }),
);

p1Visuals.push(
  bandBarChart({
    key: "p1-bands",
    x: 808,
    y: 600,
    width: 520,
    height: 400,
    title: "Procesos por rango de monto",
    subtitle: "Monto referencial en soles; “Sin monto” = no informado",
    alt: "Barras con la cantidad de procesos en cada rango de monto referencial.",
  }),
);

p1Visuals.push(
  donutChart({
    key: "p1-mype",
    x: 1344,
    y: 600,
    width: 544,
    height: 400,
    title: "Participación MYPE por monto",
    subtitle: "Cuota del monto convocado; la heurística solo aplica a bienes y servicios",
    alt: "Dona con la participación de los procesos compatibles MYPE en el monto total convocado.",
  }),
);

p1Visuals.push(
  textbox({
    key: "p1-footer-left",
    x: 32,
    y: 1016,
    width: 1232,
    height: 40,
    paragraphs: [
      paragraph(
        "Fuente: OECE — Portal de Contrataciones Abiertas (OCDS), datos abiertos CC BY 4.0. Elaboración: ContrataMYPE. Montos en soles.",
        9,
        C.inkTertiary,
      ),
    ],
  }),
);

p1Visuals.push(
  textbox({
    key: "p1-footer-right",
    x: 1288,
    y: 1016,
    width: 600,
    height: 40,
    paragraphs: [
      paragraph("MYPE = heurística de compatibilidad, no elegibilidad legal.", 9, C.amber, { align: "right", bold: true }),
    ],
  }),
);

p1Visuals.forEach((visual) => writeVisual(P1, visual));

// ---------------------------------------------------------------------------
// Page 2 — Oportunidades
// ---------------------------------------------------------------------------

writePage(P2, "Oportunidades", [
  categoricalFilter({
    key: "p2-cohort",
    entity: "Tenders",
    property: "Año de cohorte",
    values: [2024, 2025],
  }),
  categoricalFilter({
    key: "page2-mype",
    entity: "Tenders",
    property: "Compatible MYPE",
    values: [true],
  }),
]);

const p2Visuals = [];

p2Visuals.push(
  textbox({
    key: "p2-title",
    x: 32,
    y: 24,
    width: 1040,
    height: 64,
    paragraphs: [paragraph("Oportunidades compatibles MYPE", 32, C.navy, { family: "Segoe UI Semibold", bold: true })],
  }),
);

p2Visuals.push(
  textbox({
    key: "p2-source",
    x: 1088,
    y: 24,
    width: 520,
    height: 64,
    paragraphs: [
      paragraph("Cohortes 2024–2025 · mype_fit = true", 10, C.inkSecondary, { align: "right" }),
      paragraph("Vista histórica; para oportunidades vigentes usa la web app", 10, C.inkSecondary, { align: "right" }),
    ],
  }),
);

p2Visuals.push(
  navButton({
    key: "p2-nav",
    x: 1664,
    y: 32,
    width: 224,
    height: 48,
    label: "Volver al mercado",
    targetPageId: P1,
    tooltip: "Volver a la página de mercado",
    icon: "leftArrow",
    iconPlacement: "left",
    alt: "Botón para volver a la página de mercado",
  }),
);

const p2Kpis = [
  { key: "opportunities", measure: "Oportunidades MYPE", label: "Oportunidades en vista", color: C.teal, accent: C.teal, displayUnits: "1", precision: 0, alt: "Tarjeta con las oportunidades MYPE que cumplen los filtros." },
  { key: "amount", measure: "Monto MYPE", label: "Monto en vista", color: C.navy, accent: C.blue, displayUnits: "1000000", precision: 1, alt: "Tarjeta con el monto de las oportunidades que cumplen los filtros." },
  { key: "ticket", measure: "Ticket promedio", label: "Ticket promedio", color: C.inkSecondary, accent: C.inkTertiary, displayUnits: "1000", precision: 0, alt: "Tarjeta con el ticket promedio de las oportunidades que cumplen los filtros." },
];

p2Kpis.forEach((kpi, index) => {
  p2Visuals.push(
    cardVisual({
      key: `p2-${kpi.key}`,
      x: 368 + index * 512,
      y: 112,
      width: 496,
      height: 96,
      measureName: kpi.measure,
      label: kpi.label,
      valueHex: kpi.color,
      accentHex: kpi.accent,
      alt: kpi.alt,
      displayUnits: kpi.displayUnits ?? null,
      precision: kpi.precision ?? 0,
    }),
  );
});

p2Visuals.push(
  textbox({
    key: "p2-filter-title",
    x: 32,
    y: 112,
    width: 312,
    height: 32,
    paragraphs: [paragraph("Filtros", 12, C.navy, { family: "Segoe UI Semibold", bold: true })],
  }),
);

const slicers = [
  { key: "year", property: "Año de cohorte", header: "Año de cohorte", y: 160, alt: "Selector para filtrar por cohorte: todos, 2024 o 2025." },
  { key: "department", property: "Departamento", header: "Departamento", y: 256, alt: "Selector para filtrar por departamento." },
  { key: "category", property: "Categoría", header: "Categoría", y: 352, alt: "Selector para filtrar por categoría." },
  { key: "method", property: "Método", header: "Método", y: 448, alt: "Selector para filtrar por método de contratación." },
  { key: "band", property: "Rango de monto", header: "Rango de monto (S/)", y: 544, alt: "Selector para filtrar por rango de monto." },
];

slicers.forEach((slicer) => {
  p2Visuals.push(
    slicerVisual({
      key: `p2-${slicer.key}`,
      x: 32,
      y: slicer.y,
      width: 312,
      height: 80,
      property: slicer.property,
      header: slicer.header,
      alt: slicer.alt,
    }),
  );
});

p2Visuals.push(
  textbox({
    key: "p2-filter-note",
    x: 32,
    y: 648,
    width: 312,
    height: 200,
    paragraphs: [
      paragraph("Los filtros se combinan entre sí y actualizan los indicadores y la tabla.", 10, C.inkSecondary),
      paragraph("", 6, C.inkSecondary),
      paragraph("Cohortes históricas 2024–2025. No es una lista de oportunidades vigentes ni un dictamen de elegibilidad.", 10, C.amber, { bold: true }),
    ],
  }),
);

p2Visuals.push(
  tableVisual({
    key: "p2-table",
    x: 368,
    y: 224,
    width: 1520,
    height: 784,
    title: "Explorador de oportunidades",
    subtitle: "Cohortes 2024–2025; ordenado por fecha de publicación (más reciente primero); monto 0 = no informado",
    values: [
      { field: column("Tenders", "Proceso"), queryRef: "Tenders.Proceso", native: "Proceso" },
      { field: column("Buyers", "Entidad"), queryRef: "Buyers.Entidad", native: "Entidad" },
      { field: column("Tenders", "Departamento"), queryRef: "Tenders.Departamento", native: "Departamento" },
      { field: column("Tenders", "Categoría"), queryRef: "Tenders.Categoría", native: "Categoría" },
      { field: column("Tenders", "Año de cohorte"), queryRef: "Tenders.Año de cohorte", native: "Año de cohorte" },
      { field: column("Tenders", "Método"), queryRef: "Tenders.Método", native: "Método" },
      { field: column("Tenders", "Monto (S/)"), queryRef: "Tenders.Monto (S/)", native: "Monto (S/)" },
      { field: column("Tenders", "Fecha de publicación"), queryRef: "Tenders.Fecha de publicación", native: "Fecha de publicación" },
      { field: column("Tenders", "Fin del período"), queryRef: "Tenders.Fin del período", native: "Fin del período" },
    ],
    widths: [
      { queryRef: "Tenders.Proceso", width: 340 },
      { queryRef: "Buyers.Entidad", width: 270 },
      { queryRef: "Tenders.Departamento", width: 110 },
      { queryRef: "Tenders.Categoría", width: 90 },
      { queryRef: "Tenders.Año de cohorte", width: 80 },
      { queryRef: "Tenders.Método", width: 170 },
      { queryRef: "Tenders.Monto (S/)", width: 110 },
      { queryRef: "Tenders.Fecha de publicación", width: 100 },
      { queryRef: "Tenders.Fin del período", width: 100 },
    ],
    sortBy: column("Tenders", "Fecha de publicación"),
    sortDirection: "Descending",
    alt: "Tabla explorable de oportunidades compatibles MYPE con entidad, departamento, categoría, método, monto y fechas.",
    fontSize: 9,
    titleSize: 13,
    outerPadding: 12,
    columnAlignments: [
      { queryRef: "Tenders.Año de cohorte", alignment: "Right" },
      { queryRef: "Tenders.Monto (S/)", alignment: "Right" },
    ],
  }),
);

p2Visuals.push(
  textbox({
    key: "p2-footer-left",
    x: 32,
    y: 1024,
    width: 1232,
    height: 32,
    paragraphs: [
      paragraph(
        "Fuente: OECE — Portal de Contrataciones Abiertas (OCDS), datos abiertos CC BY 4.0. Elaboración: ContrataMYPE.",
        9,
        C.inkTertiary,
      ),
    ],
  }),
);

p2Visuals.push(
  textbox({
    key: "p2-footer-right",
    x: 1288,
    y: 1024,
    width: 600,
    height: 32,
    paragraphs: [
      paragraph("MYPE = heurística de compatibilidad, no elegibilidad legal.", 9, C.amber, { align: "right", bold: true }),
    ],
  }),
);

p2Visuals.forEach((visual) => writeVisual(P2, visual));

fs.writeFileSync(
  path.join(ROOT, "pages", "pages.json"),
  `${JSON.stringify(
    {
      $schema: SCHEMA_PAGES,
      pageOrder: [P1, P2],
      activePageName: P1,
    },
    null,
    2,
  )}\n`,
  "utf8",
);

console.log(`Report pages and visuals written: ${p1Visuals.length + p2Visuals.length} visuals.`);
