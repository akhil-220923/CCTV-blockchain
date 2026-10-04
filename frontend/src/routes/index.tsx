import { createFileRoute } from "@tanstack/react-router";
import {
  Activity, AlertTriangle, BadgeCheck, Blocks, Camera, CheckCircle2, ChevronRight, CircleDot,
  ClipboardCheck, Copy, Database, FileCheck2, Fingerprint, Focus, Maximize2,
  Play, Radio, RefreshCw, ScanLine, Shield, ShieldAlert, ShieldCheck, Siren,
  Upload, Users, Video,
} from "lucide-react";
import { useEffect, useRef, useState, type PointerEvent as ReactPointerEvent, type ReactNode } from "react";
import ridgeImage from "@/assets/ibvap-ridge-surveillance.jpg";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "IBVAP — Intelligent Border Video Analytics Platform" },
      { name: "description", content: "AI-driven border surveillance, personnel authentication and decentralized forensic evidence command center." },
      { property: "og:title", content: "IBVAP — Intelligent Border Video Analytics Platform" },
      { property: "og:description", content: "Intelligent border surveillance, authentication and decentralized evidence verification." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: IbvapApp,
});

type TabId = "surveillance" | "evidence" | "ledger" | "tamper" | "personnel";
const tabs: { id: TabId; short: string; label: string; icon: typeof Camera }[] = [
  { id: "surveillance", short: "LIVE", label: "Live Surveillance", icon: Camera },
  { id: "evidence", short: "VAULT", label: "Evidence Vault", icon: FileCheck2 },
  { id: "ledger", short: "CHAIN", label: "3-Node Ledger", icon: Blocks },
  { id: "tamper", short: "TEST", label: "Tamper Suite", icon: ShieldAlert },
  { id: "personnel", short: "PKI", label: "Personnel PKI", icon: Fingerprint },
];

interface OverviewMetrics {
  total_intrusions: number;
  authentic_intrusions_count?: number;
  active_intrusions_count?: number;
  tampered_intrusions_count?: number;
  chain_height: number;
  audit_logs_count: number;
  authorized_personnel_count: number;
  active_security_alerts: number;
  is_tampered: boolean;
}

interface NodeSummary {
  node_id: string;
  chain_height: number;
  integrity_valid: boolean;
  active_security_alerts: number;
  tampered_intrusions?: string[];
}

interface OverviewData {
  status: string;
  system_time: number;
  metrics: OverviewMetrics;
  nodes?: {
    border_police: NodeSummary;
    state_police: NodeSummary;
    judiciary: NodeSummary;
  };
}

interface IntrusionEvent {
  event_id: string;
  camera_id: string;
  track_id: number;
  frame_number: number;
  video_timestamp: string;
  frame_hash: string;
  camera_signature: string;
  model_hash: string;
  zone_id: string;
  evidence_file?: string;
  evidence_url?: string;
  detection_status: string;
  is_tampered: boolean;
  tamper_note?: string;
  tampered_nodes?: string[];
  node_statuses?: Record<string, string>;
  block_index?: number;
}

interface BlockTransaction {
  type: string;
  [key: string]: any;
}

interface BlockItem {
  index: number;
  hash: string;
  previous_hash: string;
  merkle_root: string;
  timestamp: number;
  validator_node: string;
  transactions: BlockTransaction[];
}

interface AuditEntry {
  audit_id: string;
  timestamp: number;
  accessor_node: string;
  accessor_identity: string;
  action: string;
  target_id: string;
  status: string;
  details: string;
  entry_hash: string;
  prev_log_hash?: string;
}

interface PersonnelMember {
  personnel_id: string;
  name: string;
  rank: string;
  organization: string;
  exemption_active: boolean;
  assigned_track_id: number | null;
}

interface ForensicResult {
  event_id: string;
  camera_id: string;
  track_id: number;
  video_timestamp: string;
  evidence_file: string;
  file_exists: boolean;
  stored_frame_hash: string;
  current_frame_hash: string;
  hash_matches: boolean;
  camera_signature: string;
  signature_valid: boolean;
  model_hash: string;
  model_registered: boolean;
  detection_status: string;
  is_concealed_tamper: boolean;
  tamper_reason: string;
  block_index: number;
  is_authentic_forensic_evidence: boolean;
  node_breakdown?: Record<string, string>;
}

function IbvapApp() {
  const [tab, setTab] = useState<TabId>("surveillance");
  const [clock, setClock] = useState("07:05:00");
  const [toast, setToast] = useState("");
  const [scanning, setScanning] = useState(false);
  const [overview, setOverview] = useState<OverviewData | null>(null);
  const [events, setEvents] = useState<IntrusionEvent[]>([]);
  const [personnel, setPersonnel] = useState<PersonnelMember[]>([]);
  const progressRef = useRef<HTMLDivElement | null>(null);
  const panelRef = useRef<HTMLDivElement | null>(null);
  const [reveal, setReveal] = useState({ x: "50%", y: "0%", nonce: 0 });

  const notify = (text: string) => {
    setToast(text);
    window.setTimeout(() => setToast(""), 3500);
  };

  // Select tab with reveal animation
  const selectTab = (next: TabId, event: ReactPointerEvent<HTMLButtonElement> | { currentTarget: HTMLButtonElement }) => {
    const rect = (event.currentTarget as HTMLButtonElement).getBoundingClientRect();
    const host = panelRef.current?.getBoundingClientRect();
    const x = host ? ((rect.left + rect.width / 2 - host.left) / host.width) * 100 : 50;
    const y = host ? ((rect.top + rect.height / 2 - host.top) / host.height) * 100 : 0;
    setReveal((prev) => ({ x: `${x.toFixed(1)}%`, y: `${y.toFixed(1)}%`, nonce: prev.nonce + 1 }));
    setTab(next);
  };

  // Clock
  useEffect(() => {
    const timer = window.setInterval(() => setClock(new Date().toISOString().slice(11, 19)), 1000);
    return () => window.clearInterval(timer);
  }, []);

  // Fetch overview metrics
  const fetchOverview = async () => {
    try {
      const res = await fetch("/api/overview");
      if (res.ok) {
        const data = await res.json();
        setOverview(data);
      }
    } catch (e) {
      console.error("Overview fetch error:", e);
    }
  };

  // Fetch events
  const fetchEvents = async () => {
    try {
      const res = await fetch("/api/events");
      if (res.ok) {
        const data = await res.json();
        setEvents(data.events || []);
      }
    } catch (e) {
      console.error("Events fetch error:", e);
    }
  };

  // Fetch personnel
  const fetchPersonnel = async () => {
    try {
      const res = await fetch("/api/personnel");
      if (res.ok) {
        const data = await res.json();
        setPersonnel(data.authorized_personnel || []);
      }
    } catch (e) {
      console.error("Personnel fetch error:", e);
    }
  };

  // Initial & periodic refresh
  useEffect(() => {
    fetchOverview();
    fetchEvents();
    fetchPersonnel();
    const interval = window.setInterval(() => {
      fetchOverview();
      fetchEvents();
    }, 3000);
    return () => window.clearInterval(interval);
  }, []);

  // Scroll animations
  useEffect(() => {
    const observer = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-revealed");
          observer.unobserve(entry.target);
        }
      }
    }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });
    document.querySelectorAll<HTMLElement>("[data-reveal]:not(.is-revealed)").forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  });

  // Parallax & scroll progress
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    let raf = 0;
    const update = () => {
      raf = 0;
      const scrollY = window.scrollY;
      document.querySelectorAll<HTMLElement>("[data-parallax]").forEach((el) => {
        const speed = Number(el.dataset["parallax"]) || 0;
        el.style.transform = `translate3d(0, ${(-scrollY * speed).toFixed(1)}px, 0)`;
      });
      const max = document.documentElement.scrollHeight - window.innerHeight;
      const progress = max > 0 ? Math.min(1, scrollY / max) : 0;
      if (progressRef.current) progressRef.current.style.transform = `scaleX(${progress})`;
      document.documentElement.style.setProperty("--scroll", progress.toFixed(3));
    };
    const onScroll = () => { if (!raf) raf = window.requestAnimationFrame(update); };
    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    return () => { window.removeEventListener("scroll", onScroll); window.removeEventListener("resize", onScroll); if (raf) cancelAnimationFrame(raf); };
  }, []);

  // Re-scan video handler
  const rescan = async () => {
    setScanning(true);
    notify("Processing video through YOLOv8-LLVIP & ByteTrack pipeline...");
    try {
      const res = await fetch("/api/process-video", { method: "POST" });
      const data = await res.json();
      setScanning(false);
      notify(data.message || `Scan complete — ${data.total_intrusions} unique intrusions anchored.`);
      fetchOverview();
      fetchEvents();
    } catch (err) {
      setScanning(false);
      notify("Scan error: " + String(err));
    }
  };

  const isBreached = Boolean(overview?.metrics?.is_tampered || (overview?.metrics?.active_security_alerts ?? 0) > 0);

  return (
    <main className="min-h-screen bg-background text-foreground">
      <div ref={progressRef} aria-hidden="true" className="scroll-progress" />
      <Header clock={clock} onEnter={() => document.getElementById("command-deck")?.scrollIntoView({ behavior: "smooth" })} />
      <Overview onEnter={() => document.getElementById("command-deck")?.scrollIntoView({ behavior: "smooth" })} />

      <section id="dashboard" className="scroll-reactive border-t border-border bg-background py-16 text-foreground">
        <div className="mx-auto max-w-[1500px] px-4 md:px-7">
          <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
            <div className="text-reveal"><Eyebrow>Live operational telemetry</Eyebrow><h2 className="mt-2 text-3xl font-bold md:text-4xl">Dashboard</h2></div>
            <span className="font-mono text-[10px] text-muted-foreground">SESSION // BP-HQ-04 // CLEARANCE ALPHA</span>
          </div>
          <div className="grid grid-cols-2 overflow-hidden rounded-lg border border-border bg-card lg:grid-cols-4">
            <Metric
              icon={<Siren />}
              label="Unique intrusions"
              value={overview?.metrics?.total_intrusions ?? events.length}
              note={isBreached ? `${overview?.metrics?.tampered_intrusions_count || 1} Concealed by Tampering` : "De-duplicated · anti-spam"}
              tone={isBreached ? "danger" : "danger"}
              delay={0}
            />
            <Metric
              icon={<Blocks />}
              label="Blockchain height"
              value={overview?.metrics?.chain_height ?? 7}
              note="7 authentic blocks anchored"
              delay={90}
            />
            <Metric
              icon={<ShieldCheck />}
              label="Consensus mesh"
              value={isBreached ? "2 / 3" : "3 / 3"}
              note={isBreached ? "Disparity flagged by consensus" : "All 3 authority nodes valid"}
              tone={isBreached ? "danger" : "success"}
              delay={180}
            />
            <Metric
              icon={<Users />}
              label="PKI personnel"
              value={overview?.metrics?.authorized_personnel_count ?? personnel.length}
              note="Exempt from perimeter alarms"
              tone="purple"
              delay={270}
            />
          </div>
        </div>
      </section>

      <section id="command-deck" className="scroll-reactive border-y border-border bg-secondary py-16 text-foreground">
        <div className="mx-auto max-w-[1500px] px-4 md:px-7">
          <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
            <div className="text-reveal"><Eyebrow>Unified security workflow</Eyebrow><h2 className="mt-2 text-3xl font-bold md:text-4xl">Command center</h2></div>
            <span className="font-mono text-[10px] text-muted-foreground">SESSION // BP-HQ-04 // CLEARANCE ALPHA</span>
          </div>
          <div className="flex overflow-x-auto border-b border-border" role="tablist" aria-label="Security center">
            {tabs.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  role="tab"
                  aria-selected={tab === item.id}
                  onClick={(event) => selectTab(item.id, event)}
                  className={cn(
                    "flex min-w-fit items-center gap-2 border-b-2 px-4 py-3 text-xs font-semibold transition-colors",
                    tab === item.id ? "border-primary text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"
                  )}
                >
                  <Icon size={15} />
                  <span className="hidden sm:inline">{item.label}</span>
                  <span className="sm:hidden">{item.short}</span>
                </button>
              );
            })}
          </div>
          <div
            ref={panelRef}
            key={`${tab}-${reveal.nonce}`}
            className="click-reveal pt-6"
            style={{ ["--cx" as string]: reveal.x, ["--cy" as string]: reveal.y }}
          >
            {tab === "surveillance" && (
              <Surveillance
                scanning={scanning}
                events={events}
                onRescan={rescan}
                onEvidence={() => setTab("evidence")}
              />
            )}
            {tab === "evidence" && (
              <Evidence
                events={events}
                breach={isBreached}
                notify={notify}
                onRefreshEvents={fetchEvents}
              />
            )}
            {tab === "ledger" && (
              <Ledger
                overview={overview}
                notify={notify}
              />
            )}
            {tab === "tamper" && (
              <Tamper
                events={events}
                breach={isBreached}
                overview={overview}
                notify={notify}
                onRefreshAll={() => {
                  fetchOverview();
                  fetchEvents();
                }}
              />
            )}
            {tab === "personnel" && (
              <Personnel
                personnel={personnel}
                notify={notify}
                onRefreshPersonnel={fetchPersonnel}
                onRefreshOverview={fetchOverview}
              />
            )}
          </div>
        </div>
      </section>
      <footer className="flex flex-col justify-between gap-2 border-t border-border px-6 py-6 font-mono text-[10px] text-muted-foreground sm:flex-row">
        <span>IBVAP · INTELLIGENT BORDER VIDEO ANALYTICS PLATFORM</span>
        <span>AI PERCEPTION · PKI AUTHENTICATION · 3-NODE CONSENSUS</span>
      </footer>
      <div
        aria-live="polite"
        className={cn(
          "fixed bottom-5 right-5 z-50 max-w-sm rounded-md border border-primary/40 bg-command px-4 py-3 text-xs text-command-foreground shadow-glow transition-all",
          toast ? "translate-y-0 opacity-100" : "pointer-events-none translate-y-8 opacity-0"
        )}
      >
        {toast}
      </div>
    </main>
  );
}

function Header({ clock, onEnter }: { clock: string; onEnter: () => void }) {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/90 backdrop-blur-xl">
      <div className="mx-auto flex min-h-[70px] max-w-[1180px] items-center justify-between gap-4 px-5">
        <a href="#top" aria-label="IBVAP home" className="shrink-0">
          <div className="text-xl font-black tracking-[0.14em]">IBV<span className="text-primary">AP</span></div>
          <div className="mt-0.5 hidden text-[8px] uppercase text-muted-foreground md:block">Decentralized border surveillance</div>
        </a>

        <div className="flex items-center gap-3">
          <span className="hidden font-mono text-[9px] text-muted-foreground xl:inline">
            <span className="text-success">●</span> {clock} UTC
          </span>
          <Button onClick={onEnter}>Enter Security Center</Button>
        </div>
      </div>
    </header>
  );
}

function Overview({ onEnter }: { onEnter: () => void }) {
  return (
    <section id="top" className="relative overflow-hidden border-b border-border bg-background">
      <div aria-hidden="true" className="hero-aurora scroll-hue" />
      <div aria-hidden="true" data-parallax="0.12" className="pointer-events-none absolute -left-24 top-16 z-0 size-80 rounded-full bg-primary/10 blur-3xl" />
      <div aria-hidden="true" data-parallax="0.2" className="pointer-events-none absolute -right-20 bottom-8 z-0 size-96 rounded-full bg-primary/5 blur-3xl" />
      <div id="platform" className="relative mx-auto grid min-h-[610px] max-w-[1180px] items-center gap-8 px-5 py-16 md:grid-cols-[0.95fr_1.05fr] lg:gap-12">
        <div>
          <div className="text-reveal text-reveal-1"><Eyebrow>Border intelligence. Independently verified.</Eyebrow></div>
          <h1 className="mt-5 max-w-xl text-4xl font-black leading-[1.05] md:text-6xl">
            <span className="block"><Words text="Intelligent border" /></span>
            <span className="block text-primary dynamic-underline"><Words text="video analytics." offset={2} /></span>
          </h1>
          <p className="text-reveal text-reveal-4 mt-6 max-w-xl text-sm leading-7 text-muted-foreground md:text-base">
            IBVAP combines real-time CCTV perception, zero-knowledge evidence anchoring, and a decentralized three-node consensus ledger across Border Police, State Police, and Judiciary.
          </p>
          <div className="text-reveal text-reveal-5 mt-8 flex flex-wrap gap-2">
            <Button onClick={onEnter}><Play size={14} /> Start Security Operation</Button>
            <Button variant="secondary" onClick={() => document.getElementById("dashboard")?.scrollIntoView({ behavior: "smooth", block: "center" })}>Dashboard <Activity size={14}/></Button>
          </div>
        </div>
        <div className="monitor-enter"><SampleCameraFrame hero /></div>
      </div>
    </section>
  );
}

function Words({ text, offset = 0 }: { text: string; offset?: number }) {
  return <>{text.split(" ").map((word, i) => <span key={`${word}-${i}`} className="word-wrap"><span className="word" style={{ ["--i" as string]: i + offset }}>{word}</span>{i < text.split(" ").length - 1 ? "\u00A0" : ""}</span>)}</>;
}

function Tilt({ children }: { children: ReactNode }) {
  const ref = useRef<HTMLDivElement | null>(null);
  const onMove = (event: ReactPointerEvent<HTMLDivElement>) => {
    const node = ref.current;
    if (!node) return;
    const rect = node.getBoundingClientRect();
    const px = (event.clientX - rect.left) / rect.width;
    const py = (event.clientY - rect.top) / rect.height;
    node.style.setProperty("--ry", `${(px - 0.5) * 12}deg`);
    node.style.setProperty("--rx", `${(0.5 - py) * 12}deg`);
    node.style.setProperty("--mx", `${px * 100}%`);
    node.style.setProperty("--my", `${py * 100}%`);
    node.style.setProperty("--sheen", "1");
    node.classList.add("is-tilting");
  };
  const reset = () => {
    const node = ref.current;
    if (!node) return;
    node.style.setProperty("--rx", "0deg");
    node.style.setProperty("--ry", "0deg");
    node.style.setProperty("--sheen", "0");
    node.classList.remove("is-tilting");
  };
  return <div ref={ref} onPointerMove={onMove} onPointerLeave={reset} className="tilt tilt-sheen relative rounded-lg">{children}</div>;
}

function Metric({ icon, label, value, note, tone = "primary", delay = 0 }: { icon: ReactNode; label: string; value: ReactNode; note: string; tone?: string; delay?: number }) {
  return (
    <div data-reveal style={{ transitionDelay: `${delay}ms` }} className="reveal-up lift border-b border-r border-border p-4 last:border-r-0 lg:border-b-0">
      <div className={cn("mb-5", tone === "danger" ? "text-destructive" : tone === "success" ? "text-success" : tone === "purple" ? "text-judicial" : "text-primary")}>
        {icon}
      </div>
      <p className="text-[10px] uppercase text-muted-foreground">{label}</p>
      <p className="mt-1 font-display text-2xl font-bold">{value}</p>
      <p className="mt-2 font-mono text-[9px] text-muted-foreground">{note}</p>
    </div>
  );
}

function SampleCameraFrame({ hero = false }: { hero?: boolean }) {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.muted = true;
      videoRef.current.play().catch(() => {});
    }
  }, []);

  return (
    <div className={cn("overflow-hidden rounded-[22px] border border-command-border bg-command p-4 shadow-panel", hero && "monitor-float")}>
      <div className="mb-3 flex items-center justify-between border-b border-command-border pb-3 font-mono text-[10px] text-command-foreground">
        <b>CAM-001 · SECTOR-4 RIDGE POST</b>
        <span className="text-success flex items-center gap-1.5 font-bold">
          <span className="inline-block size-2 rounded-full bg-success animate-pulse" />
          ACTUAL AI SURVEILLANCE FEED
        </span>
      </div>
      <div className="group relative aspect-[16/9] overflow-hidden rounded-md bg-black">
        <video
          ref={videoRef}
          src="/video/annotated"
          poster={ridgeImage}
          autoPlay
          loop
          muted
          playsInline
          preload="auto"
          className="h-full w-full object-cover"
        />
        <div className="absolute inset-0 bg-grid opacity-20 pointer-events-none" />
        <div className="absolute inset-x-0 h-px animate-scan bg-primary shadow-glow pointer-events-none" />
        <div className="absolute bottom-3 left-3 flex flex-wrap gap-1 font-mono text-[8px] pointer-events-none">
          <span className="bg-command/85 px-2 py-1 text-primary">YOLOv8-LLVIP + BYTETRACK</span>
          <span className="bg-command/85 px-2 py-1 text-warning">ZONE: RESTRICTED ROAD</span>
          <span className="bg-command/85 px-2 py-1 text-success">ED25519: SIGNED</span>
        </div>
      </div>
      <div className="mt-2 grid grid-cols-3 gap-2 font-mono text-[9px]">
        <Mini label="AI INFERENCE" value="LIVE ANNOTATED" />
        <Mini label="SURVEILLANCE" value="25 FPS CCTV" />
        <Mini label="BLOCKCHAIN" value="3 NODES MESH" />
      </div>
    </div>
  );
}

function CameraFrame({ mode = "ai" }: { mode?: "ai" | "raw" | "mp4" }) {
  const [streamFallback, setStreamFallback] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    setStreamFallback(false);
  }, [mode]);

  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.muted = true;
      videoRef.current.play().catch(() => {});
    }
  }, [mode, streamFallback]);

  return (
    <div className="overflow-hidden rounded-[22px] border border-command-border bg-command p-4 shadow-panel">
      <div className="mb-3 flex items-center justify-between border-b border-command-border pb-3 font-mono text-[10px] text-command-foreground">
        <b>CAM-001 · SECTOR-4 RIDGE POST</b>
        <span className="text-success flex items-center gap-1.5 font-bold">
          <span className="inline-block size-2 rounded-full bg-success animate-pulse" />
          {mode === "raw" ? "RAW CCTV STREAM" : mode === "mp4" ? "H.264 MP4 RECORDING" : "AI INFERENCE STREAM"}
        </span>
      </div>
      <div className="group relative aspect-[16/9] overflow-hidden rounded-md bg-black">
        {mode === "ai" && !streamFallback && (
          <img
            key="stream-ai"
            src="/video/stream/annotated"
            alt="CCTV AI Inference Feed"
            className="h-full w-full object-cover"
            onError={() => setStreamFallback(true)}
          />
        )}
        {mode === "ai" && streamFallback && (
          <video
            ref={videoRef}
            key="video-ai-fallback"
            src="/video/annotated"
            controls
            autoPlay
            loop
            muted
            playsInline
            preload="auto"
            className="h-full w-full object-cover"
          />
        )}
        {mode === "raw" && (
          <video
            ref={videoRef}
            key="video-raw"
            src="/video/raw"
            controls
            autoPlay
            loop
            muted
            playsInline
            preload="auto"
            className="h-full w-full object-cover"
          />
        )}
        {mode === "mp4" && (
          <video
            ref={videoRef}
            key="video-mp4"
            src="/video/annotated"
            controls
            autoPlay
            loop
            muted
            playsInline
            preload="auto"
            className="h-full w-full object-cover"
          />
        )}
        <div className="absolute bottom-3 left-3 flex flex-wrap gap-1 font-mono text-[8px] pointer-events-none">
          <span className="bg-command/85 px-2 py-1 text-primary">
            {mode === "raw" ? "BYTE TRACK: STANDBY" : "BYTE TRACK: ACTIVE"}
          </span>
          <span className="bg-command/85 px-2 py-1 text-warning">ZONE: RESTRICTED ROAD</span>
          <span className="bg-command/85 px-2 py-1 text-success">ED25519: SIGNED</span>
        </div>
      </div>
      <div className="mt-2 grid grid-cols-3 gap-2 font-mono text-[9px]">
        <Mini label="AI DETECTION" value={mode === "raw" ? "RAW CCTV" : "YOLOv8-LLVIP"} />
        <Mini label="ANTI-SPAM" value={mode === "raw" ? "BYPASSED" : "DWELL FILTERED"} />
        <Mini label="BLOCKCHAIN" value="3 NODES MESH" />
      </div>
    </div>
  );
}

function Mini({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-command-subtle p-2 text-command-muted">
      <span>{label}</span>
      <b className="mt-1 block text-command-foreground">{value}</b>
    </div>
  );
}

function Eyebrow({ children }: { children: ReactNode }) {
  return <div className="font-display text-[10px] font-bold uppercase tracking-[0.18em] text-primary">{children}</div>;
}

function Panel({ children, className }: { children: ReactNode; className?: string }) {
  return <section data-reveal className={cn("reveal-up lift rounded-lg border border-command-border bg-command-panel p-4", className)}>{children}</section>;
}

function PanelTitle({ icon, title, aside }: { icon: ReactNode; title: string; aside?: ReactNode }) {
  return (
    <div className="mb-4 flex items-center justify-between gap-2 border-b border-command-border pb-3">
      <div className="flex items-center gap-2 font-display text-sm font-bold">
        <span className="text-primary">{icon}</span>{title}
      </div>
      {aside}
    </div>
  );
}

function Surveillance({
  scanning,
  events,
  onRescan,
  onEvidence,
}: {
  scanning: boolean;
  events: IntrusionEvent[];
  onRescan: () => void;
  onEvidence: () => void;
}) {
  const [mode, setMode] = useState<"ai" | "raw" | "mp4">("ai");
  const [uploading, setUploading] = useState(false);
  const videoInputRef = useRef<HTMLInputElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);

  const handleVideoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    const fd = new FormData();
    fd.append("file", file);
    fd.append("set_active", "true");
    try {
      const res = await fetch("/api/upload/video", { method: "POST", body: fd });
      const data = await res.json();
      if (res.ok) {
        onRescan();
      } else {
        alert(data.error || "Upload failed");
      }
    } catch (err) {
      alert("Network error during video upload: " + err);
    } finally {
      setUploading(false);
      if (videoInputRef.current) videoInputRef.current.value = "";
    }
  };

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    const fd = new FormData();
    fd.append("file", file);
    try {
      const res = await fetch("/api/upload/image", { method: "POST", body: fd });
      const data = await res.json();
      if (res.ok) {
        alert(`Snapshot Analyzed: ${data.total_persons_detected} persons detected.\nSHA-256: ${data.sha256_hash.slice(0, 24)}...`);
      } else {
        alert(data.error || "Image analysis failed");
      }
    } catch (err) {
      alert("Network error during snapshot upload: " + err);
    } finally {
      setUploading(false);
      if (imageInputRef.current) imageInputRef.current.value = "";
    }
  };

  return (
    <div className="grid gap-4 xl:grid-cols-[1fr_380px]">
      <Panel>
        <PanelTitle
          icon={<Video size={17}/>}
          title="Dual-stream video console"
          aside={
            <div className="flex gap-1">
              <Button size="sm" variant={mode === "ai" ? "primary" : "secondary"} onClick={() => setMode("ai")}>AI Live</Button>
              <Button size="sm" variant={mode === "raw" ? "primary" : "secondary"} onClick={() => setMode("raw")}>Raw CCTV</Button>
              <Button size="sm" variant={mode === "mp4" ? "primary" : "secondary"} onClick={() => setMode("mp4")}>H.264 MP4</Button>
            </div>
          }
        />
        <CameraFrame mode={mode} />
        <div className="mt-4 flex flex-wrap justify-between items-center gap-2">
          <span className="font-mono text-[10px] text-muted-foreground">Source: Sector-4 Ridge Camera (25 FPS)</span>
          <div className="flex flex-wrap items-center gap-2">
            <input
              type="file"
              ref={videoInputRef}
              accept="video/mp4,video/mkv,video/avi,video/quicktime"
              className="hidden"
              onChange={handleVideoUpload}
            />
            <input
              type="file"
              ref={imageInputRef}
              accept="image/jpeg,image/png,image/bmp"
              className="hidden"
              onChange={handleImageUpload}
            />
            <Button
              size="sm"
              variant="outline"
              onClick={() => videoInputRef.current?.click()}
              disabled={uploading || scanning}
            >
              <Upload size={13} className="mr-1" />
              {uploading ? "Uploading..." : "Upload CCTV"}
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => imageInputRef.current?.click()}
              disabled={uploading || scanning}
            >
              <Camera size={13} className="mr-1" />
              Test Frame
            </Button>
            <Button onClick={onRescan} disabled={scanning || uploading}>
              <RefreshCw className={cn(scanning && "animate-spin")} size={14}/>
              {scanning ? "Processing video with AI..." : "Re-scan video"}
            </Button>
          </div>
        </div>
      </Panel>
      <Panel>
        <PanelTitle
          icon={<Radio size={17}/>}
          title="Intrusion event feed"
          aside={<span className="font-mono text-[9px] text-success">LIVE CONSENSUS</span>}
        />
        <p className="mb-4 text-[11px] leading-5 text-command-muted">
          First entry into restricted perimeter anchors to blockchain. Subsequent dwell frames are de-duplicated by ByteTrack.
        </p>
        <div className="space-y-2 max-h-[520px] overflow-y-auto">
          {events.length === 0 ? (
            <div className="text-xs text-muted-foreground p-3">No intrusion events recorded yet.</div>
          ) : (
            events.map((event) => {
              const isTampered = event.is_tampered || event.detection_status === "NO_INTRUSION_DETECTED";
              return (
                <article
                  key={event.event_id}
                  className={cn(
                    "rounded-md border p-3 transition-colors",
                    isTampered
                      ? "border-destructive/60 bg-destructive/10"
                      : "border-command-border bg-command-subtle hover:border-primary/50"
                  )}
                >
                  <div className="flex items-center justify-between">
                    <b className={cn("font-mono text-[11px]", isTampered ? "text-destructive" : "text-primary")}>
                      {event.event_id}
                    </b>
                    <span className={cn(
                      "rounded-sm px-1.5 py-0.5 font-mono text-[8px] font-bold uppercase",
                      isTampered ? "bg-destructive text-destructive-foreground animate-alert" : "bg-destructive/20 text-destructive"
                    )}>
                      {isTampered ? "NO INTRUSION (TAMPERED)" : "INTRUSION DETECTED"}
                    </span>
                  </div>

                  {event.evidence_url && (
                    <div className="mt-2.5 relative aspect-[16/9] overflow-hidden rounded-md border border-command-border bg-black/60">
                      <img
                        src={event.evidence_url}
                        alt={`Perimeter Intrusion Evidence ${event.event_id}`}
                        className="h-full w-full object-cover"
                        loading="lazy"
                      />
                      <span className="absolute bottom-1.5 right-1.5 bg-black/85 px-2 py-0.5 font-mono text-[8px] text-white rounded">
                        FRAME #{event.frame_number}
                      </span>
                      <span className="absolute top-1.5 left-1.5 bg-primary/90 px-1.5 py-0.5 font-mono text-[8px] text-primary-foreground font-bold rounded">
                        ED25519 SIGNED
                      </span>
                    </div>
                  )}

                  <div className="mt-2 grid grid-cols-2 gap-2 font-mono text-[9px] text-command-muted">
                    <span>TRACK #{event.track_id}</span>
                    <span>{event.video_timestamp} UTC</span>
                    <span className="col-span-2">FRAME #{event.frame_number} · BLOCK #{event.block_index ?? 4}</span>
                  </div>
                  {event.tamper_note && (
                    <div className="mt-2 text-[9px] text-destructive font-mono">
                      {event.tamper_note}
                    </div>
                  )}
                  <button onClick={onEvidence} className="mt-3 flex items-center gap-1 text-[10px] font-bold text-primary hover:underline">
                    View in forensic vault <ChevronRight size={12}/>
                  </button>
                </article>
              );
            })
          )}
        </div>
      </Panel>
    </div>
  );
}

function Evidence({
  events,
  breach,
  notify,
  onRefreshEvents,
}: {
  events: IntrusionEvent[];
  breach: boolean;
  notify: (s: string) => void;
  onRefreshEvents: () => void;
}) {
  const [selected, setSelected] = useState<string | null>(null);
  const [forensicData, setForensicData] = useState<ForensicResult | null>(null);
  const [loadingForensics, setLoadingForensics] = useState(false);

  const scrutinizeEvent = async (eventId: string) => {
    setSelected(eventId);
    setLoadingForensics(true);
    try {
      const res = await fetch(`/api/verify/evidence/${eventId}`);
      if (res.ok) {
        const data = await res.json();
        setForensicData(data);
      }
    } catch (e) {
      console.error("Forensic scrutiny error:", e);
    } finally {
      setLoadingForensics(false);
    }
  };

  return (
    <div>
      <div className="mb-5 flex justify-between items-center">
        <div>
          <Eyebrow>Chain of custody</Eyebrow>
          <h3 className="mt-2 font-display text-2xl font-bold">Forensic evidence vault</h3>
        </div>
        <Button variant="secondary" size="sm" onClick={onRefreshEvents}>
          <RefreshCw size={13}/> Refresh vault
        </Button>
      </div>

      {events.length === 0 ? (
        <Panel className="text-center py-12">
          <FileCheck2 className="size-10 text-muted-foreground mx-auto mb-3" />
          <h4 className="font-display text-base font-bold">No evidence frames captured yet</h4>
          <p className="mt-1 font-mono text-xs text-muted-foreground max-w-md mx-auto">
            Click "Re-scan video for intrusions" in the Live Surveillance console to run YOLOv8 on CCTV footage and automatically anchor forensic intrusion frames.
          </p>
          <Button className="mt-4" size="sm" onClick={onRefreshEvents}>
            <RefreshCw size={13} /> Refresh Evidence Vault
          </Button>
        </Panel>
      ) : (
        <div className="grid gap-4 lg:grid-cols-3">
          {events.map((e) => {
            const isTampered = e.is_tampered || e.detection_status === "NO_INTRUSION_DETECTED";
            return (
              <Panel key={e.event_id} className={isTampered ? "border-destructive/60" : ""}>
              <div className="relative aspect-[16/9] overflow-hidden rounded-md bg-command-subtle">
                <img
                  src={e.evidence_url || `/evidence/evidence_${e.event_id}_frame${e.frame_number}.jpg`}
                  alt={`Evidence frame ${e.event_id}`}
                  loading="lazy"
                  className={cn("h-full w-full object-cover", isTampered && "contrast-125")}
                  onError={(ev) => { (ev.target as HTMLImageElement).src = ridgeImage; }}
                />
                <span className={cn(
                  "absolute left-2 top-2 px-2 py-1 font-mono text-[8px] font-bold text-white",
                  isTampered ? "bg-destructive animate-alert" : "bg-primary/90"
                )}>
                  {isTampered ? "CONCEALED ON PEER" : "EVIDENCE CAPTURE"}
                </span>
                <span className="absolute right-2 bottom-2 bg-black/80 px-2 py-0.5 font-mono text-[8px] text-white">
                  FRAME #{e.frame_number}
                </span>
              </div>
              <div className="mt-4 flex items-start justify-between gap-4">
                <div>
                  <h4 className="font-display text-sm font-bold">{e.event_id}</h4>
                  <p className="mt-1 font-mono text-[9px] text-command-muted">
                    TRACK #{e.track_id} · {e.camera_id} · {e.video_timestamp} UTC
                  </p>
                </div>
                <Button size="sm" onClick={() => scrutinizeEvent(e.event_id)}>
                  <Focus size={13}/> Scrutinize
                </Button>
              </div>
              <div className="mt-4 space-y-1.5 font-mono text-[9px] text-command-muted">
                <p className="truncate" title={e.frame_hash}>
                  SHA-256 <span className="text-command-foreground">{e.frame_hash.slice(0, 16)}…</span>
                </p>
                <p>
                  ED25519 <span className="text-success">CAMERA SIGNATURE VERIFIED</span>
                </p>
                <p>
                  STATUS <span className={isTampered ? "text-destructive font-bold" : "text-success"}>
                    {isTampered ? "TAMPERED: NO INTRUSION DETECTED" : "ANCHORED (BLOCK #" + (e.block_index ?? 4) + ")"}
                  </span>
                </p>
              </div>
            </Panel>
          );
        })}
      </div>
      )}

      {selected && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/80 p-4" role="dialog" aria-modal="true">
          <Panel className="w-full max-w-2xl shadow-glow">
            <PanelTitle
              icon={<ClipboardCheck size={18}/>}
              title={`Judicial forensic scrutiny · ${selected}`}
              aside={<Button size="sm" variant="ghost" onClick={() => setSelected(null)}>Close</Button>}
            />
            {loadingForensics ? (
              <div className="py-12 text-center text-sm text-muted-foreground">
                <RefreshCw className="animate-spin inline-block mr-2" size={16}/> Running cryptographic verification with Judiciary Node...
              </div>
            ) : forensicData ? (
              <>
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="relative aspect-[4/3] rounded-md overflow-hidden bg-black">
                    <img
                      src={`/evidence/${forensicData.evidence_file.split("/").pop()}`}
                      alt="Forensic evidence enlargement"
                      className="h-full w-full object-cover"
                      onError={(ev) => { (ev.target as HTMLImageElement).src = ridgeImage; }}
                    />
                  </div>
                  <div className="space-y-2">
                    <CheckRow label="On-chain stored hash" value={forensicData.stored_frame_hash.slice(0, 12) + "…"} ok={true} />
                    <CheckRow label="Disk frame SHA-256" value={forensicData.current_frame_hash.slice(0, 12) + "…"} ok={forensicData.hash_matches} />
                    <CheckRow label="Camera Ed25519 sig" value={forensicData.signature_valid ? "VALID" : "INVALID"} ok={forensicData.signature_valid} />
                    <CheckRow label="AI model certification" value={forensicData.model_registered ? "CERTIFIED" : "UNAUTHORIZED"} ok={forensicData.model_registered} />
                    <CheckRow
                      label="Cross-node consensus"
                      value={forensicData.is_concealed_tamper ? "CONCEALED ON PEER" : "3 / 3 CONSISTENT"}
                      ok={!forensicData.is_concealed_tamper}
                    />
                  </div>
                </div>

                <div className={cn(
                  "mt-4 border p-4 text-center font-display text-xs font-bold uppercase tracking-wider",
                  forensicData.is_authentic_forensic_evidence
                    ? "border-success/40 bg-success/10 text-success"
                    : "border-destructive bg-destructive/15 text-destructive"
                )}>
                  {forensicData.is_authentic_forensic_evidence
                    ? "APPROVED · SECTION 65B CERTIFIED FORENSIC EVIDENCE (LEGALLY ADMISSIBLE)"
                    : `REJECTED · ${forensicData.tamper_reason || "TAMPERING DETECTED / EVIDENCE INADMISSIBLE"}`}
                </div>

                <div className="mt-4 flex gap-2">
                  <Button className="w-full" onClick={() => notify("Verification report sealed and added to the audit trail.")}>
                    <FileCheck2 size={14}/> Seal verification report
                  </Button>
                </div>
              </>
            ) : null}
          </Panel>
        </div>
      )}
    </div>
  );
}

function CheckRow({ label, value, ok }: { label: string; value: string; ok: boolean }) {
  return (
    <div className="flex items-center justify-between rounded-md bg-command-subtle p-2.5 text-[10px]">
      <span className="text-command-muted font-mono">{label}</span>
      <b className={cn("font-mono", ok ? "text-success" : "text-destructive")}>{value}</b>
    </div>
  );
}

function Ledger({
  overview,
  notify,
}: {
  overview: OverviewData | null;
  notify: (s: string) => void;
}) {
  const [selectedNode, setSelectedNode] = useState<string>("border_police");
  const [chainBlocks, setChainBlocks] = useState<BlockItem[]>([]);
  const [selectedBlock, setSelectedBlock] = useState<BlockItem | null>(null);
  const [isChainValid, setIsChainValid] = useState<boolean>(true);

  const fetchChain = async (nodeKey: string) => {
    try {
      const res = await fetch(`/api/blockchain/chain?node=${nodeKey}`);
      if (res.ok) {
        const data = await res.json();
        setChainBlocks(data.chain || []);
        setIsChainValid(data.is_integrity_valid ?? true);
      }
    } catch (e) {
      console.error("Chain fetch error:", e);
    }
  };

  useEffect(() => {
    fetchChain(selectedNode);
  }, [selectedNode]);

  const nodes = [
    {
      key: "border_police",
      name: "Border Police Node",
      org: "Border Security Force (BSF)",
      port: "8001",
      role: "CCTV Ingestion & Stream Key Auth",
      summary: overview?.nodes?.border_police,
    },
    {
      key: "state_police",
      name: "State Police Node",
      org: "State Police HQ",
      port: "8002",
      role: "Regional Law Enforcement & Audit",
      summary: overview?.nodes?.state_police,
    },
    {
      key: "judiciary",
      name: "Judiciary Node",
      org: "High Court / Judicial Tribunal",
      port: "8003",
      role: "Model Certification & Forensics Scrutiny",
      summary: overview?.nodes?.judiciary,
    },
  ];

  return (
    <div className="space-y-4">
      {/* 3 Node Cards */}
      <div className="grid gap-3 md:grid-cols-3">
        {nodes.map((n) => {
          const isSelected = selectedNode === n.key;
          const isCompromised = !n.summary?.integrity_valid || (n.summary?.tampered_intrusions && n.summary.tampered_intrusions.length > 0);
          const hasAlert = (n.summary?.active_security_alerts ?? 0) > 0;

          return (
            <div key={n.key} onClick={() => setSelectedNode(n.key)} className="cursor-pointer">
              <Tilt>
                <Panel className={cn(
                  "transition-all",
                  isSelected && "ring-2 ring-primary",
                  isCompromised && "border-destructive bg-destructive/5"
                )}>
                  <div className="flex justify-between items-center">
                    <Database className={isCompromised ? "text-destructive" : "text-primary"} size={20} />
                    <span className={cn(
                      "font-mono text-[9px] font-bold px-2 py-0.5 rounded",
                      isCompromised
                        ? "bg-destructive text-destructive-foreground animate-alert"
                        : hasAlert
                        ? "bg-warning text-warning-foreground"
                        : "bg-success/20 text-success"
                    )}>
                      {isCompromised ? "🚨 COMPROMISED" : hasAlert ? "⚠️ PEER ALERT" : "● VALID"}
                    </span>
                  </div>
                  <h3 className="mt-4 font-display text-base font-bold">{n.name}</h3>
                  <p className="text-[10px] text-command-muted font-mono">{n.org} · PORT {n.port}</p>
                  <p className="mt-2 text-xs text-muted-foreground">{n.role}</p>
                  <div className="mt-4 grid grid-cols-2 gap-2 font-mono text-[9px]">
                    <Mini label="CHAIN HEIGHT" value={`${n.summary?.chain_height ?? 7} BLOCKS`} />
                    <Mini label="NODE STATUS" value={isCompromised ? "TAMPERED" : "SYNCED"} />
                  </div>
                </Panel>
              </Tilt>
            </div>
          );
        })}
      </div>

      {/* Explorer Panel */}
      <Panel>
        <PanelTitle
          icon={<Blocks size={17}/>}
          title={`Blockchain explorer · ${selectedNode.replace("_", " ").toUpperCase()}`}
          aside={
            <span className={cn(
              "font-mono text-[9px] font-bold px-2 py-0.5 rounded",
              isChainValid ? "text-success bg-success/15" : "text-destructive bg-destructive/15"
            )}>
              {isChainValid ? "CHAIN INTEGRITY 100% VALID" : "CHAIN COMPROMISED"}
            </span>
          }
        />

        <div className="overflow-x-auto">
          <table className="w-full min-w-[820px] text-left font-mono text-[10px]">
            <thead className="text-command-muted">
              <tr>
                {["Height", "Block hash", "Previous hash", "Merkle root", "Validator", "TX", "Timestamp"].map((x) => (
                  <th key={x} className="border-b border-command-border p-3 font-normal">{x}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {chainBlocks.slice().reverse().map((b) => {
                const isTamperedBlock = b.transactions.some(
                  (tx) => tx.tampered || tx.detection_status === "NO_INTRUSION_DETECTED" || tx.type === "MALICIOUS_INJECTION"
                );

                return (
                  <tr
                    key={b.index}
                    onClick={() => setSelectedBlock(b)}
                    className={cn(
                      "cursor-pointer transition-colors",
                      isTamperedBlock
                        ? "bg-destructive/15 hover:bg-destructive/25 text-destructive font-bold"
                        : "hover:bg-command-subtle"
                    )}
                  >
                    <td className="p-3 text-primary">#{b.index}</td>
                    <td className="p-3" title={b.hash}>{b.hash.slice(0, 14)}…</td>
                    <td className="p-3 text-command-muted" title={b.previous_hash}>{b.previous_hash.slice(0, 14)}…</td>
                    <td className="p-3 text-command-muted" title={b.merkle_root}>{b.merkle_root.slice(0, 14)}…</td>
                    <td className="p-3">{b.validator_node}</td>
                    <td className="p-3">
                      {isTamperedBlock ? (
                        <span className="text-destructive font-bold">🚨 TAMPERED</span>
                      ) : (
                        `${b.transactions.length} TX`
                      )}
                    </td>
                    <td className="p-3">{new Date(b.timestamp * 1000).toLocaleTimeString()}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Panel>

      {/* Block Inspector */}
      {selectedBlock && (
        <Panel>
          <PanelTitle
            icon={<CircleDot size={17}/>}
            title={`Block #${selectedBlock.index} inspector`}
            aside={<Button size="sm" variant="ghost" onClick={() => setSelectedBlock(null)}>Close</Button>}
          />
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            {selectedBlock.transactions.map((tx, i) => (
              <div key={i} className="rounded-md border border-command-border bg-command-subtle p-3">
                <span className="font-mono text-[9px] text-primary">TRANSACTION 0{i + 1}</span>
                <p className="mt-1 text-[11px] font-bold">{tx.type}</p>
                <div className="mt-2 font-mono text-[8px] space-y-1 text-command-muted">
                  {tx.event_id && <p>EVENT: {tx.event_id}</p>}
                  {tx.track_id && <p>TRACK ID: #{tx.track_id}</p>}
                  {tx.camera_id && <p>CAMERA: {tx.camera_id}</p>}
                  {tx.model_id && <p>MODEL: {tx.model_id}</p>}
                  {tx.personnel_id && <p>PERSONNEL: {tx.personnel_id}</p>}
                  {tx.detection_status && (
                    <p className={tx.detection_status === "NO_INTRUSION_DETECTED" ? "text-destructive font-bold" : "text-success"}>
                      STATUS: {tx.detection_status}
                    </p>
                  )}
                  {tx.frame_hash && <p className="truncate">HASH: {tx.frame_hash.slice(0, 20)}…</p>}
                </div>
              </div>
            ))}
          </div>
          <Button
            variant="secondary"
            size="sm"
            className="mt-4"
            onClick={() => {
              navigator.clipboard?.writeText(selectedBlock.hash);
              notify(`Copied block #${selectedBlock.index} hash to clipboard.`);
            }}
          >
            <Copy size={13}/> Copy block hash
          </Button>
        </Panel>
      )}
    </div>
  );
}

function Tamper({
  events,
  breach,
  overview,
  notify,
  onRefreshAll,
}: {
  events: IntrusionEvent[];
  breach: boolean;
  overview: OverviewData | null;
  notify: (s: string) => void;
  onRefreshAll: () => void;
}) {
  const [selectedEventId, setSelectedEventId] = useState<string>("INTRUSION-DET-001");
  const [selectedNode, setSelectedNode] = useState<string>("state_police");
  const [auditNode, setAuditNode] = useState<string>("border_police");
  const [auditLogs, setAuditLogs] = useState<AuditEntry[]>([]);
  const [tamperMatrix, setTamperMatrix] = useState<{
    targetNode: string;
    eventId: string;
    peer1: string;
    peer2: string;
    action: string;
  } | null>(null);

  const fetchAuditLogs = async (nodeKey: string) => {
    try {
      const res = await fetch(`/api/audit-logs?node=${nodeKey}`);
      if (res.ok) {
        const data = await res.json();
        setAuditLogs(data.audit_logs || []);
      }
    } catch (e) {
      console.error("Audit log error:", e);
    }
  };

  useEffect(() => {
    fetchAuditLogs(auditNode);
  }, [auditNode]);

  const attackIntrusionConcealment = async () => {
    const targetNodeName = selectedNode === "state_police" ? "StatePolice-Node" : selectedNode === "border_police" ? "BorderPolice-Node" : "Judiciary-Node";
    const all = ["BorderPolice-Node", "StatePolice-Node", "Judiciary-Node"];
    const peers = all.filter((x) => x !== targetNodeName);

    try {
      const res = await fetch("/api/intrusion/change-status", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          event_id: selectedEventId,
          node: selectedNode,
          status: "NO_INTRUSION_DETECTED",
        }),
      });
      const data = await res.json();
      setTamperMatrix({
        targetNode: targetNodeName,
        eventId: selectedEventId,
        peer1: peers[0],
        peer2: peers[1],
        action: "TAMPER",
      });
      notify(`Intrusion ${selectedEventId} altered to 'NO INTRUSION DETECTED' on ${targetNodeName}. Disparity caught by consensus!`);
      onRefreshAll();
      fetchAuditLogs(auditNode);
    } catch (err) {
      notify("Tamper error: " + String(err));
    }
  };

  const restoreIntrusionConcealment = async () => {
    try {
      const res = await fetch("/api/intrusion/change-status", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          event_id: selectedEventId,
          node: selectedNode,
          status: "INTRUSION_DETECTED",
        }),
      });
      setTamperMatrix(null);
      notify(`Intrusion ${selectedEventId} restored to 'INTRUSION DETECTED'. All nodes synchronized!`);
      onRefreshAll();
      fetchAuditLogs(auditNode);
    } catch (err) {
      notify("Restore error: " + String(err));
    }
  };

  const simulateEvidenceTamper = async () => {
    try {
      const res = await fetch("/api/simulate/tamper-evidence", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ event_id: selectedEventId }),
      });
      const data = await res.json();
      notify("Evidence byte alteration caught! Frame hash mismatch flagged by Judiciary.");
      onRefreshAll();
      fetchAuditLogs(auditNode);
    } catch (err) {
      notify("Error: " + String(err));
    }
  };

  const simulateAuditTamper = async () => {
    try {
      const res = await fetch("/api/simulate/tamper", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target: "audit_log", node: selectedNode }),
      });
      const data = await res.json();
      notify("Audit log record altered! Peer nodes rejected unauthorized tampering.");
      onRefreshAll();
      fetchAuditLogs(auditNode);
    } catch (err) {
      notify("Error: " + String(err));
    }
  };

  const restoreAllNodes = async () => {
    try {
      const res = await fetch("/api/simulate/restore", { method: "POST" });
      setTamperMatrix(null);
      notify("All 3 authority nodes restored to authentic cryptographic state!");
      onRefreshAll();
      fetchAuditLogs(auditNode);
    } catch (err) {
      notify("Error: " + String(err));
    }
  };

  const testAuditAccessBroadcast = async () => {
    try {
      const res = await fetch("/api/audit-logs/access", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          node: auditNode,
          role: "External-Oversight-Auditor",
          action: "INSPECT_AUDIT_LOGS",
          target_id: "ALL_AUDIT_ENTRIES",
        }),
      });
      const data = await res.json();
      notify(data.message || "Audit access logged and broadcast to peer nodes!");
      fetchAuditLogs(auditNode);
    } catch (err) {
      notify("Audit broadcast error: " + String(err));
    }
  };

  return (
    <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
      {/* Primary Demonstration: Intrusion Concealment Attack */}
      <Panel>
        <PanelTitle icon={<ShieldAlert size={18}/>} title="Perimeter breach concealment attack" />
        <p className="mb-4 text-xs leading-6 text-command-muted">
          Simulate an adversary modifying the ledger on one node to change <strong>'INTRUSION DETECTED'</strong> into <strong>'NO INTRUSION DETECTED'</strong> so that intrusion detection is not found. Watch how decentralized consensus immediately catches the disparity!
        </p>
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="text-[10px] text-command-muted">
            INTRUSION EVENT
            <select
              value={selectedEventId}
              onChange={(e) => setSelectedEventId(e.target.value)}
              className="mt-2 h-10 w-full rounded-md border border-command-border bg-command-subtle px-3 text-xs text-command-foreground"
            >
              {events.map((ev) => (
                <option key={ev.event_id} value={ev.event_id}>
                  {ev.event_id} (Track #{ev.track_id} - {ev.video_timestamp})
                </option>
              ))}
            </select>
          </label>
          <label className="text-[10px] text-command-muted">
            NODE TO ATTACK
            <select
              value={selectedNode}
              onChange={(e) => setSelectedNode(e.target.value)}
              className="mt-2 h-10 w-full rounded-md border border-command-border bg-command-subtle px-3 text-xs text-command-foreground"
            >
              <option value="state_police">State Police Node (Regional HQ)</option>
              <option value="border_police">Border Police Node (BSF Tactical)</option>
              <option value="judiciary">Judiciary Node (Tribunal)</option>
            </select>
          </label>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <Button variant="danger" onClick={attackIntrusionConcealment}>
            <Siren size={14}/> Tamper: conceal intrusion
          </Button>
          <Button variant="secondary" onClick={restoreIntrusionConcealment}>
            <RefreshCw size={14}/> Restore intrusion status
          </Button>
        </div>

        {/* Dynamic Tamper Matrix */}
        {tamperMatrix ? (
          <div className="mt-5 rounded-md border border-destructive bg-destructive/10 p-4 font-mono text-[10px]">
            <p className="font-display text-sm font-bold text-destructive">
              🚨 CRITICAL CONSENSUS BREACH: TAMPERING DETECTED!
            </p>
            <div className="mt-2 space-y-1 text-command-muted">
              <p className="text-destructive font-bold">
                • {tamperMatrix.targetNode}: Status altered to 'NO INTRUSION DETECTED' (Concealment attempt).
              </p>
              <p className="text-success font-bold">
                • {tamperMatrix.peer1}: Status remains 'INTRUSION DETECTED' (Disparity caught by consensus).
              </p>
              <p className="text-success font-bold">
                • {tamperMatrix.peer2}: Status remains 'INTRUSION DETECTED' (Disparity caught by consensus).
              </p>
            </div>
            <p className="mt-3 text-warning font-bold border-t border-destructive/30 pt-2">
              Consensus Ruling: 2/3 Byzantine Fault Tolerant Majority REJECTS the malicious modification!
            </p>
          </div>
        ) : (
          <div className="mt-5 rounded-md border border-success/40 bg-success/5 p-4">
            <p className="font-display text-sm font-bold text-success">
              ✓ CONSENSUS CRYPTOGRAPHICALLY AUTHENTIC
            </p>
            <p className="mt-2 text-[11px] leading-5 text-command-muted">
              All 3 authority nodes agree on intrusion status, video timestamps, and frame hashes.
            </p>
          </div>
        )}
      </Panel>

      {/* Secondary Demonstrations */}
      <Panel>
        <PanelTitle icon={<AlertTriangle size={18}/>} title="Secondary tamper simulations" />
        <div className="space-y-3">
          <ActionRow
            title="Evidence file tampering"
            detail="Bit-flip the forensic evidence JPEG on disk and verify with Judiciary node."
            button="Simulate"
            onClick={simulateEvidenceTamper}
          />
          <ActionRow
            title="Audit log tampering"
            detail="Mutate an immutable inspection record on State Police node."
            button="Simulate"
            onClick={simulateAuditTamper}
          />
          <ActionRow
            title="Authentic state recovery"
            detail="Recompute Merkle roots, sync all 3 peers and clear security alerts."
            button="Restore all nodes"
            onClick={restoreAllNodes}
            safe
          />
        </div>
      </Panel>

      {/* Cross-Node Audit Log */}
      <Panel className="xl:col-span-2">
        <PanelTitle
          icon={<ClipboardCheck size={18}/>}
          title="Cross-node audit log & transparency"
          aside={
            <div className="flex gap-2 items-center flex-wrap">
              <span className="text-[10px] text-command-muted">Node:</span>
              <Button size="sm" variant={auditNode === "border_police" ? "primary" : "ghost"} onClick={() => setAuditNode("border_police")}>Border Police</Button>
              <Button size="sm" variant={auditNode === "state_police" ? "primary" : "ghost"} onClick={() => setAuditNode("state_police")}>State Police</Button>
              <Button size="sm" variant={auditNode === "judiciary" ? "primary" : "ghost"} onClick={() => setAuditNode("judiciary")}>Judiciary</Button>
              <Button size="sm" variant="outline" onClick={testAuditAccessBroadcast}>
                <Radio size={12}/> Test Access Broadcast
              </Button>
            </div>
          }
        />
        <div className="overflow-x-auto max-h-[360px] overflow-y-auto">
          <table className="w-full min-w-[760px] font-mono text-[9px]">
            <thead className="text-command-muted sticky top-0 bg-command-panel">
              <tr>
                {["Audit ID", "Timestamp", "Accessor", "Node", "Action", "Target", "Entry SHA-256", "Status"].map((x) => (
                  <th key={x} className="border-b border-command-border p-3 text-left font-normal">{x}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {auditLogs.slice().reverse().map((entry) => {
                const isAlarm = entry.status && (entry.status.includes("TAMPER") || entry.status.includes("ALARM"));
                return (
                  <tr key={entry.audit_id} className={isAlarm ? "bg-destructive/15 text-destructive font-bold" : "hover:bg-command-subtle"}>
                    <td className="p-3 text-primary">{entry.audit_id}</td>
                    <td className="p-3">{new Date(entry.timestamp * 1000).toLocaleTimeString()}</td>
                    <td className="p-3">{entry.accessor_identity}</td>
                    <td className="p-3">{entry.accessor_node}</td>
                    <td className="p-3"><code>{entry.action}</code></td>
                    <td className="p-3">{entry.target_id}</td>
                    <td className="p-3" title={entry.entry_hash}>{entry.entry_hash.slice(0, 14)}…</td>
                    <td className={cn("p-3 font-bold", isAlarm ? "text-destructive" : "text-success")}>
                      {entry.status}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}

function ActionRow({ title, detail, button, onClick, safe }: { title: string; detail: string; button: string; onClick: () => void; safe?: boolean }) {
  return (
    <div className="flex flex-col justify-between gap-3 rounded-md border border-command-border bg-command-subtle p-4 sm:flex-row sm:items-center">
      <div>
        <b className="text-xs">{title}</b>
        <p className="mt-1 text-[10px] text-command-muted">{detail}</p>
      </div>
      <Button size="sm" variant={safe ? "secondary" : "warning"} onClick={onClick}>
        {button}
      </Button>
    </div>
  );
}

function Personnel({
  personnel,
  notify,
  onRefreshPersonnel,
  onRefreshOverview,
}: {
  personnel: PersonnelMember[];
  notify: (s: string) => void;
  onRefreshPersonnel: () => void;
  onRefreshOverview: () => void;
}) {
  const [form, setForm] = useState({ id: "", name: "", rank: "", track: "" });
  const [submitting, setSubmitting] = useState(false);

  const toggleClearance = async (p: PersonnelMember) => {
    const updatedStatus = !p.exemption_active;
    try {
      const res = await fetch("/api/personnel/authorize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          personnel_id: p.personnel_id,
          name: p.name,
          rank: p.rank,
          assigned_track_id: p.assigned_track_id,
          exemption_active: updatedStatus,
        }),
      });
      if (res.ok) {
        notify(`${p.name} (${p.personnel_id}) clearance ${updatedStatus ? "activated" : "revoked"}.`);
        onRefreshPersonnel();
        onRefreshOverview();
      }
    } catch (e) {
      notify("Clearance toggle error: " + String(e));
    }
  };

  const submit = async () => {
    if (!form.id || !form.name) {
      notify("Personnel ID and full name are required.");
      return;
    }
    setSubmitting(true);
    try {
      const res = await fetch("/api/personnel/authorize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          personnel_id: form.id,
          name: form.name,
          rank: form.rank || "Patrol Officer",
          assigned_track_id: form.track ? parseInt(form.track) : null,
          exemption_active: true,
        }),
      });
      setSubmitting(false);
      if (res.ok) {
        notify(`Officer ${form.name} registered and anchored to all 3 nodes.`);
        setForm({ id: "", name: "", rank: "", track: "" });
        onRefreshPersonnel();
        onRefreshOverview();
      }
    } catch (e) {
      setSubmitting(false);
      notify("Registration error: " + String(e));
    }
  };

  const fields: Array<[keyof typeof form, string, string]> = [
    ["id", "Personnel ID", "BP-OFFICER-704"],
    ["name", "Full name", "Officer name"],
    ["rank", "Rank / designation", "Inspector"],
    ["track", "Assigned ByteTrack ID", "6"],
  ];

  return (
    <div className="space-y-4">
      <div className="flex gap-3 rounded-md border border-success/30 bg-success/5 p-4">
        <ShieldCheck className="shrink-0 text-success"/>
        <p className="text-xs leading-6">
          <b className="text-success">Cybersecurity Access Control Exemption.</b> Only authorized patrol personnel with registered PKI credentials are classified as <code>AUTHORIZED_ACCESS</code>. When they enter the restricted perimeter, alarms are suppressed.
        </p>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.3fr_0.7fr]">
        {/* Roster */}
        <Panel>
          <PanelTitle icon={<Users size={18}/>} title="Registered personnel roster" />
          <div className="overflow-x-auto">
            <table className="w-full min-w-[670px] text-left text-[10px]">
              <thead className="font-mono text-command-muted">
                <tr>
                  {["Personnel ID", "Full name", "Rank / Org", "Assigned Track", "Clearance"].map((x) => (
                    <th key={x} className="border-b border-command-border p-3 font-normal">{x}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {personnel.map((p) => (
                  <tr key={p.personnel_id}>
                    <td className="p-3 font-mono text-primary font-bold">{p.personnel_id}</td>
                    <td className="p-3 font-bold">{p.name}</td>
                    <td className="p-3 text-command-muted">{p.rank}<br/>{p.organization}</td>
                    <td className="p-3 font-mono">
                      {p.assigned_track_id !== null ? `Track #${p.assigned_track_id}` : "Any / Perimeter Token"}
                    </td>
                    <td className="p-3">
                      <button
                        aria-label={`Toggle clearance for ${p.name}`}
                        onClick={() => toggleClearance(p)}
                        className={cn(
                          "relative h-6 w-11 rounded-full transition-colors",
                          p.exemption_active ? "bg-success" : "bg-command-border"
                        )}
                      >
                        <span className={cn(
                          "absolute top-1 size-4 rounded-full bg-command-foreground transition-all",
                          p.exemption_active ? "left-6" : "left-1"
                        )}/>
                      </button>
                      <span className={cn("ml-2 font-mono text-[8px] font-bold", p.exemption_active ? "text-success" : "text-destructive")}>
                        {p.exemption_active ? "ACTIVE ✓" : "REVOKED"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        {/* Register Form */}
        <Panel>
          <PanelTitle icon={<BadgeCheck size={18}/>} title="Register officer clearance" />
          <div className="space-y-3">
            {fields.map(([key, label, placeholder]) => (
              <label key={key} className="block text-[10px] text-command-muted">
                {label}
                <input
                  value={form[key]}
                  onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                  placeholder={placeholder}
                  className="mt-1.5 h-10 w-full rounded-md border border-command-border bg-command-subtle px-3 text-xs text-command-foreground outline-none focus:border-primary"
                />
              </label>
            ))}
            <Button className="mt-2 w-full" onClick={submit} disabled={submitting}>
              <Blocks size={14}/> {submitting ? "Broadcasting..." : "Broadcast authorization to 3 nodes"}
            </Button>
          </div>
        </Panel>
      </div>
    </div>
  );
}