"use client";

import { MONO } from "@/lib/colors";
import { ClaimTier } from "../ClaimTier";
import { DebateMatrix } from "../DebateMatrix";
import { HoverButton } from "../Hover";
import { MessageThread } from "../MessageThread";
import { StageRail } from "../StageRail";
import { StatTile, LABEL_08_949494 } from "../StatTile";
import { SteppsBars } from "../SteppsBars";
import type { MissionVM } from "@/lib/viewmodel";

const CARD = {
  background: "#FFFFFF",
  border: "1px solid #E5E7EB",
  borderRadius: "20px",
  padding: "24px 28px",
} as const;

const SECTION_LABEL = {
  fontFamily: MONO,
  fontSize: "12px",
  lineHeight: "18px",
  fontWeight: 600,
  letterSpacing: "0.08em",
  textTransform: "uppercase" as const,
  color: "#777777",
};

const MICRO_LABEL = {
  fontFamily: MONO,
  fontSize: "10px",
  fontWeight: 600,
  letterSpacing: "0.08em",
  textTransform: "uppercase" as const,
  color: "#949494",
};

const FIELD_LABEL = {
  fontFamily: MONO,
  fontSize: "10px",
  fontWeight: 600,
  letterSpacing: "0.06em",
  textTransform: "uppercase" as const,
  color: "#949494",
};

const AUDIT_GRID = "minmax(0,1.6fr) 76px 96px minmax(0,1.2fr)";

export function RunDetail({ vm }: { vm: MissionVM }) {
  const d = vm.d;
  if (!d) return null;

  return (
    <section
      style={{
        padding: "24px 32px 80px",
        maxWidth: "1560px",
        display: "flex",
        flexDirection: "column",
        gap: "20px",
      }}
    >
      {/* ------------------------------------------------------------- header */}
      <div style={{ ...CARD, boxShadow: "0px 7px 15px rgba(17,17,17,0.03)" }}>
        <div
          style={{
            display: "flex",
            alignItems: "flex-start",
            justifyContent: "space-between",
            gap: "24px 40px",
            flexWrap: "wrap",
          }}
        >
          <div style={{ minWidth: "320px", flex: "1 1 420px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <HoverButton
                onClick={vm.goRuns}
                style={{
                  background: "none",
                  border: "none",
                  padding: 0,
                  cursor: "pointer",
                  fontSize: "12px",
                  fontWeight: 600,
                  color: "#777777",
                }}
                hoverStyle={{ color: "#703AE6" }}
              >
                ← Runs
              </HoverButton>
              <span style={{ fontSize: "12px", color: "#BFBFBF" }}>/</span>
              <span style={{ fontFamily: MONO, fontSize: "12px", color: "#4B5563" }}>
                {d.label}
              </span>
            </div>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "14px",
                marginTop: "12px",
                flexWrap: "wrap",
              }}
            >
              <h2
                style={{
                  margin: 0,
                  fontSize: "28px",
                  lineHeight: "42px",
                  fontWeight: 600,
                  letterSpacing: "-0.02em",
                  color: "#1F1F1F",
                }}
              >
                {d.headline}
              </h2>
              <span style={d.outcomePill}>{d.outcomeLabel}</span>
            </div>
            <div
              style={{
                marginTop: "8px",
                fontSize: "14px",
                lineHeight: "21px",
                color: "#4B5563",
                maxWidth: "86ch",
              }}
            >
              {d.outcomeDetail}
            </div>
          </div>
          <div style={{ flex: "0 0 auto", display: "flex", gap: "12px", flexWrap: "wrap" }}>
            {[
              { label: "Duration", value: d.duration },
              { label: "Cost", value: d.cost },
              { label: "Messages", value: d.msgCount },
            ].map((t) => (
              <StatTile
                key={t.label}
                label={t.label}
                value={t.value}
                container={{
                  background: "#F7F7F7",
                  borderRadius: "12px",
                  padding: "12px 16px",
                  minWidth: "112px",
                }}
                labelStyle={LABEL_08_949494}
                valueStyle={{
                  fontSize: "18px",
                  fontWeight: 500,
                  marginTop: "6px",
                  fontVariantNumeric: "tabular-nums",
                }}
              />
            ))}
          </div>
        </div>

        <div
          style={{
            display: "flex",
            alignItems: "flex-start",
            gap: "14px",
            padding: "14px 18px",
            marginTop: "20px",
            background: "#F1EBFD",
            borderRadius: "12px",
          }}
        >
          <span
            style={{
              fontFamily: MONO,
              fontSize: "10px",
              lineHeight: "15px",
              fontWeight: 600,
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              color: "#FFFFFF",
              background: "#703AE6",
              padding: "3px 8px",
              borderRadius: "999px",
              flex: "0 0 auto",
            }}
          >
            Inferred
          </span>
          <div style={{ fontSize: "13px", lineHeight: "20px", color: "#3E207F" }}>
            <div>{d.boundaryNote}</div>
            <div
              style={{
                fontFamily: MONO,
                fontSize: "12px",
                marginTop: "8px",
                color: "#5029A3",
              }}
            >
              open ← {d.boundaryOpen}
            </div>
            <div
              style={{
                fontFamily: MONO,
                fontSize: "12px",
                marginTop: "3px",
                color: "#5029A3",
              }}
            >
              close ← {d.boundaryClose}
            </div>
          </div>
        </div>
      </div>

      {/* --------------------------------------------------------- stage rail */}
      <StageRail stages={d.stages} note={d.stageNote} />

      {/* --------------------------------------------------------- the debate */}
      <div style={CARD}>
        <div style={SECTION_LABEL}>The debate</div>

        <div
          style={{
            display: "flex",
            alignItems: "flex-start",
            gap: "24px 48px",
            marginTop: "18px",
            padding: "24px",
            background: "#F7F7F7",
            borderRadius: "16px",
            flexWrap: "wrap",
          }}
        >
          <div style={{ flex: "1 1 380px", minWidth: 0, maxWidth: "60ch" }}>
            <div
              style={{
                fontSize: "24px",
                lineHeight: "36px",
                fontWeight: 600,
                letterSpacing: "-0.02em",
                color: d.engagedColor,
              }}
            >
              {d.engagedVerdict}
            </div>
            <p
              style={{
                margin: "6px 0 0",
                fontSize: "14px",
                lineHeight: "22px",
                color: "#4B5563",
              }}
            >
              {d.engagedDetail}
            </p>
            <div
              style={{ display: "flex", gap: "12px", marginTop: "20px", flexWrap: "wrap" }}
            >
              <StatTile
                label="Cross-replies"
                value={d.crossReplies}
                container={{
                  background: "#FFFFFF",
                  borderRadius: "12px",
                  padding: "12px 18px",
                }}
                labelStyle={LABEL_08_949494}
                valueStyle={{
                  fontSize: "22px",
                  fontWeight: 500,
                  marginTop: "4px",
                  fontVariantNumeric: "tabular-nums",
                  color: d.engagedColor,
                }}
              />
              <StatTile
                label="Pairs engaged"
                value={d.pairsEngaged}
                container={{
                  background: "#FFFFFF",
                  borderRadius: "12px",
                  padding: "12px 18px",
                }}
                labelStyle={LABEL_08_949494}
                valueStyle={{
                  fontSize: "22px",
                  fontWeight: 500,
                  marginTop: "4px",
                  fontVariantNumeric: "tabular-nums",
                }}
              />
              <StatTile
                label="Graft accepted"
                value={d.graftCount}
                container={{
                  background: "#FFFFFF",
                  borderRadius: "12px",
                  padding: "12px 18px",
                }}
                labelStyle={LABEL_08_949494}
                valueStyle={{
                  fontSize: "22px",
                  fontWeight: 500,
                  marginTop: "4px",
                  fontVariantNumeric: "tabular-nums",
                }}
              />
            </div>
          </div>

          {vm.showMatrix && <DebateMatrix cols={d.matrixCols} rows={d.matrixRows} />}
        </div>

        <div style={{ marginTop: "8px" }}>
          <MessageThread
            messages={d.messages}
            articlePadding="20px 0"
            wrapParseHeader={false}
            nowrapExpand={false}
          />
        </div>
      </div>

      {/* ----------------------------------------------------------- research */}
      {d.hasResearch && (
        <div style={CARD}>
          <div style={SECTION_LABEL}>Research</div>

          <div
            style={{
              display: "flex",
              alignItems: "flex-start",
              gap: "14px",
              padding: "16px 20px",
              marginTop: "16px",
              background: d.researchNoteBg,
              borderRadius: "16px",
              maxWidth: "104ch",
            }}
          >
            <span style={d.researchNoteChip}>{d.researchNoteLabel}</span>
            <p
              style={{
                margin: 0,
                fontSize: "14px",
                lineHeight: "22px",
                color: d.researchNoteColor,
                maxWidth: "78ch",
              }}
            >
              {d.researchNotes}
            </p>
          </div>

          <div
            style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginTop: "18px" }}
          >
            {d.keywords.map((k) => (
              <span
                key={k}
                style={{
                  fontFamily: MONO,
                  fontSize: "12px",
                  padding: "5px 12px",
                  background: "#F4F4F4",
                  borderRadius: "999px",
                  color: "#4B5563",
                }}
              >
                {k}
              </span>
            ))}
          </div>

          {d.trends.map((t) => (
            <div
              key={t.id}
              style={{
                display: "grid",
                gridTemplateColumns: "minmax(320px,1fr) minmax(260px,300px)",
                gap: "24px 48px",
                padding: "24px 0 0",
                borderTop: "1px solid #F4F4F4",
                marginTop: "24px",
              }}
            >
              <div style={{ minWidth: 0 }}>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "10px",
                    flexWrap: "wrap",
                  }}
                >
                  <span style={t.momentumStyle}>{t.momentum}</span>
                  <span style={{ fontFamily: MONO, fontSize: "12px", color: "#949494" }}>
                    {t.type} · {t.window}
                  </span>
                </div>
                <h4
                  style={{
                    margin: "12px 0 0",
                    fontSize: "20px",
                    lineHeight: "30px",
                    fontWeight: 600,
                    maxWidth: "58ch",
                    letterSpacing: "-0.01em",
                    color: "#1F1F1F",
                  }}
                >
                  {t.headline}
                </h4>
                <div
                  style={{
                    marginTop: "16px",
                    display: "grid",
                    gridTemplateColumns: "auto 1fr",
                    gap: "10px 20px",
                    fontSize: "14px",
                    maxWidth: "70ch",
                    alignItems: "baseline",
                  }}
                >
                  <div style={FIELD_LABEL}>Hook</div>
                  <div style={{ color: "#1F1F1F", lineHeight: "21px" }}>
                    “{t.hookText}” <span style={{ color: "#949494" }}>· {t.hookCategory}</span>
                  </div>
                  <div style={FIELD_LABEL}>Pattern</div>
                  <div style={{ color: "#4B5563", lineHeight: "21px" }}>
                    {t.pattern} · {t.format}
                  </div>
                  <div style={FIELD_LABEL}>Shape</div>
                  <div
                    style={{ color: t.shapeColor, lineHeight: "21px", fontWeight: 500 }}
                  >
                    {t.engagementShape}
                  </div>
                  <div style={FIELD_LABEL}>Evidence</div>
                  <div style={{ color: "#4B5563", lineHeight: "21px" }}>{t.evidence}</div>
                </div>
                <div
                  style={{
                    marginTop: "16px",
                    display: "flex",
                    flexDirection: "column",
                    gap: "8px",
                  }}
                >
                  {t.sources.map((s, i) => (
                    <div
                      key={i}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "12px",
                        fontFamily: MONO,
                        fontSize: "12px",
                      }}
                    >
                      <span style={{ color: "#949494", width: "70px", flex: "0 0 70px" }}>
                        {s.platform}
                      </span>
                      <span style={s.style}>{s.engagementText}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div
                style={{ background: "#F7F7F7", borderRadius: "16px", padding: "18px 20px" }}
              >
                <div style={MICRO_LABEL}>STEPPS</div>
                <SteppsBars
                  rows={t.stepps}
                  columns="104px 1fr 20px"
                  gap="10px"
                  rowGap="9px"
                  barHeight="6px"
                  barColor="#595959"
                  labelSize="12px"
                  labelColor="#4B5563"
                  valueColor="#1F1F1F"
                  marginTop="14px"
                />
                <div style={{ ...MICRO_LABEL, marginTop: "18px" }}>Vanna hooks</div>
                <ul
                  style={{
                    margin: "10px 0 0",
                    paddingLeft: "18px",
                    fontSize: "13px",
                    lineHeight: "20px",
                    color: "#4B5563",
                  }}
                >
                  {t.hooks.map((h, i) => (
                    <li key={i}>{h}</li>
                  ))}
                </ul>
              </div>
            </div>
          ))}

          {d.hasCompetitors && (
            <div
              style={{
                borderTop: "1px solid #F4F4F4",
                paddingTop: "20px",
                marginTop: "24px",
              }}
            >
              <div style={MICRO_LABEL}>Competitor content</div>
              <div
                style={{
                  marginTop: "12px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "8px",
                }}
              >
                {d.competitors.map((c, i) => (
                  <div
                    key={i}
                    style={{
                      display: "grid",
                      gridTemplateColumns:
                        "minmax(0,140px) minmax(0,100px) minmax(0,110px) minmax(0,1fr)",
                      gap: "16px",
                      fontSize: "13px",
                      alignItems: "center",
                    }}
                  >
                    <span
                      style={{ fontFamily: MONO, color: "#1F1F1F", fontWeight: 500 }}
                    >
                      {c.handle}
                    </span>
                    <span
                      style={{ fontFamily: MONO, color: "#949494", fontSize: "12px" }}
                    >
                      {c.posted}
                    </span>
                    <span style={{ color: "#777777" }}>{c.format}</span>
                    <span style={{ color: "#4B5563" }}>{c.note}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ------------------------------------------------------------- drafts */}
      <div style={CARD}>
        <div style={SECTION_LABEL}>Drafts</div>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
            gap: "20px",
            marginTop: "18px",
            alignItems: "start",
          }}
        >
          {d.drafts.map((p) => (
            <div
              key={p.arc}
              style={{
                borderRadius: "16px",
                background: "#F7F7F7",
                padding: "20px",
                borderTop: `3px solid ${p.hue}`,
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  justifyContent: "space-between",
                  gap: "12px",
                }}
              >
                <span
                  style={{
                    fontSize: "14px",
                    lineHeight: "20px",
                    fontWeight: 600,
                    color: p.hue,
                    wordBreak: "break-word",
                  }}
                >
                  {p.arc}
                </span>
                <span style={p.scoreStyle}>{p.scoreText}</span>
              </div>
              <div
                style={{
                  fontFamily: MONO,
                  fontSize: "11px",
                  color: "#949494",
                  marginTop: "6px",
                }}
              >
                {p.meta}
              </div>
              <div
                style={{
                  fontSize: "17px",
                  lineHeight: "26px",
                  fontWeight: 600,
                  marginTop: "16px",
                  color: "#1F1F1F",
                  letterSpacing: "-0.01em",
                }}
              >
                “{p.hook}…”
              </div>
              <div
                style={{
                  fontSize: "13px",
                  lineHeight: "21px",
                  marginTop: "10px",
                  color: "#4B5563",
                  whiteSpace: "pre-wrap",
                }}
              >
                {p.body}
              </div>
              {p.canExpand && (
                <HoverButton
                  onClick={p.toggle}
                  style={{
                    marginTop: "10px",
                    background: "#FFFFFF",
                    border: "none",
                    borderRadius: "8px",
                    padding: "6px 12px",
                    cursor: "pointer",
                    fontSize: "12px",
                    fontWeight: 600,
                    color: "#703AE6",
                    whiteSpace: "nowrap",
                  }}
                  hoverStyle={{ background: "#F1EBFD" }}
                >
                  {p.toggleLabel}
                </HoverButton>
              )}

              <div style={{ ...MICRO_LABEL, marginTop: "22px" }}>Claims</div>
              <div
                style={{
                  marginTop: "10px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "10px",
                }}
              >
                {p.claims.map((c, i) => (
                  <div
                    key={i}
                    style={{
                      display: "grid",
                      gridTemplateColumns: "22px 1fr",
                      gap: "10px",
                      alignItems: "start",
                    }}
                  >
                    <ClaimTier tier={c.tier} style={c.tierStyle} />
                    <div>
                      <div
                        style={{ fontSize: "13px", lineHeight: "20px", color: "#1F1F1F" }}
                      >
                        {c.text}
                      </div>
                      <div
                        style={{
                          fontSize: "11px",
                          color: "#949494",
                          marginTop: "4px",
                          fontFamily: MONO,
                        }}
                      >
                        {c.source}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div style={{ ...MICRO_LABEL, marginTop: "22px" }}>Self-scored STEPPS</div>
              <SteppsBars
                rows={p.stepps}
                columns="96px 1fr 18px"
                gap="9px"
                rowGap="7px"
                barHeight="5px"
                barColor={p.hue}
                labelSize="11px"
                labelColor="#777777"
                valueColor="#4B5563"
                marginTop="10px"
              />

              {p.hasKiller && (
                <div
                  style={{
                    marginTop: "20px",
                    padding: "14px 16px",
                    background: "#FFFFFF",
                    borderRadius: "12px",
                  }}
                >
                  <div style={{ ...MICRO_LABEL, color: "#E54C4F" }}>Killer issue</div>
                  <div
                    style={{
                      fontSize: "13px",
                      lineHeight: "20px",
                      marginTop: "7px",
                      color: "#4B5563",
                    }}
                  >
                    {p.killer}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
        <div
          style={{
            marginTop: "16px",
            fontSize: "12px",
            lineHeight: "18px",
            color: "#949494",
          }}
        >
          {d.draftsNote}
        </div>
      </div>

      {/* ------------------------------------------------------------- ruling */}
      <div style={CARD}>
        <div style={SECTION_LABEL}>Ruling</div>
        {d.hasRuling && (
          <div style={{ marginTop: "16px" }}>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "16px",
                flexWrap: "wrap",
              }}
            >
              <span style={d.verdictPill}>{d.verdictLabel}</span>
              <span
                style={{
                  fontSize: "14px",
                  lineHeight: "21px",
                  color: "#4B5563",
                  maxWidth: "74ch",
                }}
              >
                {d.verdictNote}
              </span>
            </div>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
                gap: "20px",
                marginTop: "24px",
              }}
            >
              {d.scoreCards.map((s) => (
                <div
                  key={s.arc}
                  style={{ background: "#F7F7F7", borderRadius: "16px", padding: "20px" }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "flex-start",
                      justifyContent: "space-between",
                      gap: "12px",
                    }}
                  >
                    <span
                      style={{
                        fontSize: "14px",
                        lineHeight: "20px",
                        fontWeight: 600,
                        color: s.hue,
                        wordBreak: "break-word",
                      }}
                    >
                      {s.arc}
                    </span>
                    <span
                      style={{
                        fontFamily: MONO,
                        fontSize: "28px",
                        lineHeight: "28px",
                        fontWeight: 600,
                        color: s.totalColor,
                        fontVariantNumeric: "tabular-nums",
                        flex: "0 0 auto",
                      }}
                    >
                      {s.total}
                    </span>
                  </div>
                  <div
                    style={{
                      marginTop: "16px",
                      display: "flex",
                      flexDirection: "column",
                      gap: "8px",
                    }}
                  >
                    {s.bars.map((b) => (
                      <div
                        key={b.label}
                        style={{
                          display: "grid",
                          gridTemplateColumns: "104px 1fr 46px",
                          gap: "10px",
                          alignItems: "center",
                        }}
                      >
                        <div style={{ fontSize: "12px", color: "#4B5563" }}>{b.label}</div>
                        <div
                          style={{
                            height: "6px",
                            background: "#DFDFDF",
                            borderRadius: "999px",
                            overflow: "hidden",
                          }}
                        >
                          <div
                            style={{
                              height: "100%",
                              width: b.pct,
                              borderRadius: "999px",
                              background: s.hue,
                            }}
                          />
                        </div>
                        <div
                          style={{
                            fontFamily: MONO,
                            fontSize: "11px",
                            textAlign: "right",
                            color: "#1F1F1F",
                            fontVariantNumeric: "tabular-nums",
                          }}
                        >
                          {b.text}
                        </div>
                      </div>
                    ))}
                  </div>
                  <div
                    style={{
                      marginTop: "16px",
                      paddingTop: "14px",
                      borderTop: "1px solid #DFDFDF",
                    }}
                  >
                    <div style={MICRO_LABEL}>Killer issue</div>
                    <div
                      style={{
                        fontSize: "13px",
                        lineHeight: "20px",
                        marginTop: "6px",
                        color: "#4B5563",
                      }}
                    >
                      {s.killer}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {d.hasGraft && (
              <div
                style={{
                  marginTop: "24px",
                  padding: "20px 24px",
                  borderRadius: "16px",
                  background: "#F1EBFD",
                }}
              >
                <div style={{ ...MICRO_LABEL, color: "#703AE6" }}>Graft</div>
                <div
                  style={{
                    fontSize: "16px",
                    lineHeight: "24px",
                    marginTop: "8px",
                    color: "#1F1F1F",
                  }}
                >
                  Took <strong style={{ fontWeight: 600 }}>{d.graftTook}</strong> from{" "}
                  <span style={{ color: d.graftHue, fontWeight: 600 }}>{d.graftFrom}</span>
                </div>
                <div
                  style={{
                    fontSize: "14px",
                    lineHeight: "22px",
                    marginTop: "6px",
                    color: "#4B5563",
                    maxWidth: "80ch",
                  }}
                >
                  {d.graftWhy}
                </div>
              </div>
            )}

            <div style={{ marginTop: "32px" }}>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "14px",
                  flexWrap: "wrap",
                }}
              >
                <div style={MICRO_LABEL}>Claim audit</div>
                <div
                  style={{ fontSize: "13px", fontWeight: 500, color: d.inflationColor }}
                >
                  {d.inflationNote}
                </div>
              </div>
              <div
                style={{
                  marginTop: "14px",
                  borderRadius: "16px",
                  overflow: "hidden",
                  border: "1px solid #E5E7EB",
                  overflowX: "auto",
                }}
              >
                <div
                  style={{
                    display: "grid",
                    minWidth: "720px",
                    gridTemplateColumns: AUDIT_GRID,
                    gap: "0 16px",
                    padding: "12px 20px",
                    background: "#111111",
                    fontFamily: MONO,
                    fontSize: "10px",
                    fontWeight: 600,
                    letterSpacing: "0.08em",
                    textTransform: "uppercase",
                    color: "#949494",
                  }}
                >
                  <div>Claim</div>
                  <div>Filed as</div>
                  <div>Found</div>
                  <div>Verified against</div>
                </div>
                {d.audit.map((a) => (
                  <div
                    key={a.key}
                    style={{
                      display: "grid",
                      minWidth: "720px",
                      gridTemplateColumns: AUDIT_GRID,
                      gap: "0 16px",
                      padding: "14px 20px",
                      borderBottom: "1px solid #F4F4F4",
                      background: a.rowBg,
                      alignItems: "center",
                    }}
                  >
                    <div
                      style={{
                        fontSize: "14px",
                        lineHeight: "21px",
                        color: "#1F1F1F",
                        paddingRight: "12px",
                      }}
                    >
                      {a.claim}
                    </div>
                    <div>
                      <ClaimTier tier={a.said} style={a.saidStyle} />
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <ClaimTier tier={a.found} style={a.foundStyle} />
                      <span
                        style={{ fontSize: "11px", fontWeight: 600, color: a.flagColor }}
                      >
                        {a.flag}
                      </span>
                    </div>
                    <div
                      style={{
                        fontFamily: MONO,
                        fontSize: "12px",
                        color: "#777777",
                        lineHeight: "18px",
                      }}
                    >
                      {a.verified}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div
              style={{
                marginTop: "24px",
                maxWidth: "82ch",
                padding: "20px 24px",
                background: "#F7F7F7",
                borderRadius: "16px",
              }}
            >
              <div style={MICRO_LABEL}>Send-back notes</div>
              <p
                style={{
                  margin: "8px 0 0",
                  fontSize: "15px",
                  lineHeight: "24px",
                  color: "#1F1F1F",
                }}
              >
                {d.sendBack}
              </p>
            </div>
          </div>
        )}
        {d.noRuling && (
          <div
            style={{
              marginTop: "14px",
              fontSize: "14px",
              lineHeight: "22px",
              color: "#777777",
              maxWidth: "74ch",
            }}
          >
            {d.noRulingText}
          </div>
        )}
      </div>

      {/* ------------------------------------------------ artifact + gate/review */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))",
          gap: "20px",
          alignItems: "stretch",
        }}
      >
        <div style={CARD}>
          <div style={SECTION_LABEL}>Artifact</div>
          {d.hasArtifact && (
            <div
              style={{
                display: "flex",
                gap: "24px",
                marginTop: "18px",
                alignItems: "flex-start",
                flexWrap: "wrap",
              }}
            >
              <div style={{ flex: "0 0 auto" }}>
                <div
                  style={{
                    width: "260px",
                    height: "260px",
                    borderRadius: "16px",
                    backgroundColor: "#F7F7F7",
                    backgroundImage:
                      "repeating-linear-gradient(135deg, #EDEDED 0 1px, transparent 1px 10px)",
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "flex-end",
                    padding: "20px",
                  }}
                >
                  <div
                    style={{
                      fontSize: "19px",
                      lineHeight: "26px",
                      color: "#1F1F1F",
                      fontWeight: 600,
                      letterSpacing: "-0.01em",
                    }}
                  >
                    {d.artHeadline}
                  </div>
                  <div
                    style={{
                      fontSize: "19px",
                      lineHeight: "26px",
                      color: d.artHue,
                      fontWeight: 600,
                      letterSpacing: "-0.01em",
                    }}
                  >
                    {d.artEmphasis}
                  </div>
                  <div
                    style={{
                      fontSize: "12px",
                      lineHeight: "18px",
                      color: "#4B5563",
                      marginTop: "8px",
                    }}
                  >
                    {d.artSubhead}
                  </div>
                  <div
                    style={{
                      fontFamily: MONO,
                      fontSize: "11px",
                      color: "#1F1F1F",
                      marginTop: "16px",
                      paddingTop: "12px",
                      borderTop: "1px solid #DFDFDF",
                    }}
                  >
                    {d.artDisclaimer}
                  </div>
                </div>
                <div
                  style={{
                    fontSize: "11px",
                    lineHeight: "17px",
                    color: "#949494",
                    marginTop: "10px",
                    maxWidth: "260px",
                  }}
                >
                  Composed from <code style={{ fontFamily: MONO }}>visual_brief</code>. The PNG
                  is on disk and needs a backend file route.
                </div>
              </div>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "auto 1fr",
                  gap: "10px 16px",
                  fontSize: "13px",
                  alignItems: "baseline",
                  minWidth: 0,
                }}
              >
                <div style={FIELD_LABEL}>File</div>
                <div
                  style={{
                    fontFamily: MONO,
                    fontSize: "12px",
                    color: "#1F1F1F",
                    wordBreak: "break-all",
                  }}
                >
                  {d.artFile}
                </div>
                <div style={FIELD_LABEL}>Size</div>
                <div style={{ fontFamily: MONO, fontSize: "12px", color: "#1F1F1F" }}>
                  {d.artSize} · {d.artType}
                </div>
                <div style={FIELD_LABEL}>Rendered</div>
                <div style={{ fontFamily: MONO, fontSize: "12px", color: "#1F1F1F" }}>
                  {d.artRendered}
                </div>
                <div style={FIELD_LABEL}>Disclaimer</div>
                <div style={{ color: "#1F1F1F", lineHeight: "20px" }}>{d.artDisclaimer}</div>
              </div>
            </div>
          )}
          {d.noArtifact && (
            <div
              style={{
                marginTop: "14px",
                fontSize: "14px",
                lineHeight: "22px",
                color: "#777777",
                maxWidth: "60ch",
              }}
            >
              {d.noArtifactText}
            </div>
          )}
        </div>

        <div style={CARD}>
          <div style={SECTION_LABEL}>Gate + review</div>
          <div
            style={{
              marginTop: "18px",
              padding: "20px",
              background: "#F7F7F7",
              borderRadius: "16px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <span style={d.gatePill}>{d.gateLabel}</span>
              <span style={{ fontSize: "13px", color: "#4B5563" }}>{d.gateSub}</span>
            </div>
            <div
              style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginTop: "14px" }}
            >
              {d.gateChecks.map((c) => (
                <span
                  key={c}
                  style={{
                    fontFamily: MONO,
                    fontSize: "11px",
                    padding: "4px 10px",
                    background: "#FFFFFF",
                    borderRadius: "999px",
                    color: "#4B5563",
                  }}
                >
                  {c}
                </span>
              ))}
            </div>
            <div
              style={{
                fontSize: "13px",
                lineHeight: "20px",
                color: "#4B5563",
                marginTop: "14px",
              }}
            >
              {d.gateNote}
            </div>
          </div>
          <div
            style={{
              marginTop: "16px",
              padding: "20px",
              background: "#F7F7F7",
              borderRadius: "16px",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "12px",
                flexWrap: "wrap",
              }}
            >
              <span style={d.reviewPill}>{d.reviewLabel}</span>
              <span style={{ fontFamily: MONO, fontSize: "12px", color: "#777777" }}>
                {d.reviewMeta}
              </span>
            </div>
            <div
              style={{
                fontSize: "14px",
                color: "#1F1F1F",
                marginTop: "14px",
                lineHeight: "22px",
              }}
            >
              {d.reviewReply}
            </div>
            <div
              style={{
                fontFamily: MONO,
                fontSize: "11px",
                color: "#949494",
                marginTop: "12px",
                wordBreak: "break-all",
              }}
            >
              {d.reviewPath}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
