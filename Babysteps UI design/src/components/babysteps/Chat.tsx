import { useEffect, useRef, useState } from "react";
import {
  ArrowLeft, ArrowUp, Mic, MicOff, Paperclip, PhoneOff, Video, VideoOff, FileText, Plus, Keyboard, Globe, MessageCircle, PanelLeft,
} from "lucide-react";
import { companions, openers, reply, tasks, type CompanionId, type TaskId } from "@/lib/companions";

import { Button } from "@/components/ui/button";
import { BerlinGuide } from "@/components/babysteps/BerlinGuide";

type Msg = { id: number; from: "ai" | "me"; text: string; file?: string | undefined };

function useIsDesktop() {
  const [desktop, setDesktop] = useState(false);
  useEffect(() => {
    const mql = window.matchMedia("(min-width: 1024px)");
    const onChange = () => setDesktop(mql.matches);
    mql.addEventListener("change", onChange);
    setDesktop(mql.matches);
    return () => mql.removeEventListener("change", onChange);
  }, []);
  return desktop;
}

export function Chat({
  companion, task, onBack, onSwitch, onNewTask,
}: { companion: CompanionId; task: TaskId; onBack: () => void; onSwitch: (c: CompanionId) => void; onNewTask: (t: TaskId) => void }) {
  const c = companions[companion];
  const [msgs, setMsgs] = useState<Msg[]>([{ id: 1, from: "ai", text: openers[task] }]);
  const [text, setText] = useState("");
  const [typing, setTyping] = useState(false);
  const [turn, setTurn] = useState(0);
  const isBerlin = task === "berlin";
  const isDesktop = useIsDesktop();
  const [video, setVideo] = useState(isBerlin);
  const [sidebar, setSidebar] = useState(false);
  const [chatOpen, setChatOpen] = useState(true);
  const [website, setWebsite] = useState(isBerlin);
  const [mic, setMic] = useState(false);
  const [cam, setCam] = useState(false);
  const [voice, setVoice] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs, typing]);
  useEffect(() => { inputRef.current?.focus(); }, []);
  useEffect(() => { if (isDesktop && !isBerlin) setSidebar(true); }, [isDesktop, isBerlin]);
  useEffect(() => { if (!notice) return; const t = setTimeout(() => setNotice(null), 3500); return () => clearTimeout(t); }, [notice]);

  const send = (body: string, file?: string) => {
    if (!body.trim() && !file) return;
    setMsgs((m) => [...m, { id: Date.now(), from: "me", text: body.trim(), file }]);
    setText("");
    setTyping(true);
    const t = turn;
    setTurn(t + 1);
    setTimeout(() => {
      setTyping(false);
      setMsgs((m) => [...m, { id: Date.now() + 1, from: "ai", text: reply(task, t) }]);
      inputRef.current?.focus();
    }, 1300);
  };

  const toggleMic = () => { setMic((v) => !v); if (!mic) setNotice("Voice isn't connected yet — please type for now."); };
  const toggleCam = () => { setCam((v) => !v); if (!cam) setNotice("Your camera isn't connected yet. Nothing is being shared."); };

  const title = task === "open" ? `Chat with ${c.name}` : tasks.find((t) => t.id === task)?.title ?? "Conversation";

  return (
    <div className="flex h-dvh flex-col overflow-hidden">
      <div className="glass flex shrink-0 flex-wrap items-center gap-1 border-x-0 border-t-0 px-3 py-2">
        <Button variant="ghost" size="icon" onClick={onBack} aria-label="Return home" title="Return home"><ArrowLeft /></Button>
        <span className="min-w-0 flex-1 truncate px-2 text-sm font-semibold">{title}</span>
      </div>
      <div className="relative flex min-h-0 flex-1 overflow-hidden">
      {/* Sidebar: overlay with backdrop on small screens, in-flow on desktop */}
      {sidebar && !isDesktop && (
        <button type="button" aria-label="Close menu" onClick={() => setSidebar(false)}
          className="absolute inset-0 z-20 animate-in fade-in duration-300 bg-foreground/30" />
      )}
      <Collapsible open={sidebar} onOpen={() => setSidebar(true)} label="Menu" icon={<PanelLeft className="size-4" />}
        className="glass border-y-0 border-l-0 max-lg:absolute max-lg:inset-y-0 max-lg:left-0 max-lg:z-30 max-lg:bg-card max-lg:shadow-float"
        openClass="w-64" barClass="w-11">
        <div className="flex h-full w-64 flex-col overflow-y-auto p-4">
          <div className="flex items-center justify-between gap-2">
            <Button variant="ghost" onClick={onBack} className="flex items-center gap-2 text-lg font-medium text-muted-foreground hover:text-foreground">
              <ArrowLeft className="size-5" /> Home
            </Button>
            <CollapseButton label="Menu" onClick={() => setSidebar(false)} />
          </div>
          <p className="mt-8 text-sm font-semibold uppercase tracking-wider text-muted-foreground">Your companion</p>
          <div className="mt-3 flex gap-3">
            {Object.values(companions).map((p) => (
              <Button variant="ghost" key={p.id} onClick={() => { onSwitch(p.id); if (!isDesktop) setSidebar(false); }} aria-pressed={p.id === companion}
                className={`flex flex-1 flex-col items-center gap-2 rounded-2xl p-3 transition ${p.id === companion ? "bg-card shadow-soft" : "opacity-60 hover:opacity-100"}`}>
                <img src={p.photo} alt="" className="size-16 rounded-full object-cover" />
                <span className="font-semibold">{p.name}</span>
              </Button>
            ))}
          </div>
          <p className="mt-8 text-sm font-semibold uppercase tracking-wider text-muted-foreground">Start something new</p>
          <nav className="mt-3 flex flex-col gap-1">
            {tasks.map((t) => (
              <Button variant="ghost" key={t.id} onClick={() => { onNewTask(t.id); if (!isDesktop) setSidebar(false); }}
                className={`rounded-xl px-4 py-3 text-left text-base transition ${t.id === task ? "bg-card font-semibold shadow-soft" : "hover:bg-card/60"}`}>
                {t.title}
              </Button>
            ))}
            <Button variant="ghost" onClick={() => { onNewTask("open"); if (!isDesktop) setSidebar(false); }} className="mt-1 flex items-center gap-2 rounded-xl px-4 py-3 text-left text-base text-primary hover:bg-card/60">
              <Plus className="size-5" /> New conversation
            </Button>
          </nav>
        </div>
      </Collapsible>

      <div className={`flex min-w-0 flex-1 flex-col gap-3 p-3 lg:flex-row ${isBerlin ? "overflow-y-auto lg:overflow-hidden" : "overflow-hidden"}`}>
        {/* Video stage */}
        <Collapsible open={video} onOpen={() => setVideo(true)} label="Video" icon={<Video className="size-4" />}
          className="rounded-lg bg-muted shadow-soft"
          openClass={isBerlin ? "h-[30dvh] lg:aspect-[4/5] lg:h-auto lg:w-[180px] lg:self-start xl:w-[220px]" : "h-[40dvh] lg:h-auto lg:flex-1"}
          barClass="h-11 lg:h-auto lg:w-11">
          <section aria-label="Companion video" className="relative h-full w-full overflow-hidden rounded-lg">
            <img src={c.photo} alt={`${c.name}'s portrait`} className={`h-full w-full ${isBerlin ? "object-contain lg:object-cover" : "object-cover"}`} />
            <div className="absolute inset-x-0 top-0 h-32 bg-gradient-to-b from-foreground/40 to-transparent" />
            <div className="absolute inset-x-0 top-0 flex items-start justify-between p-4">
              <Button variant="ghost" onClick={onBack} aria-label="Back" className="glass-dark grid size-12 place-items-center rounded-full lg:hidden"><ArrowLeft /></Button>
              <div className="glass-dark mx-auto rounded-full px-4 py-2 text-center text-sm">
                <span className="font-semibold">{c.name}</span> · Video preview
              </div>
              <div className="size-12 lg:hidden" />
            </div>
            <CollapseButton label="Video" onClick={() => { setVideo(false); setMic(false); setCam(false); }} className="glass-dark absolute left-3 top-3 hidden lg:grid" />
            <div className={`glass-dark absolute right-3 top-20 grid place-items-center rounded-lg text-xs ${isBerlin ? "h-16 w-12" : "h-28 w-20 lg:h-36 lg:w-28"}`}>
              {cam ? <span className="px-2 text-center">Camera not connected</span> : <VideoOff className="size-6 opacity-80" />}
            </div>
            <div className={`absolute inset-x-0 bottom-5 flex justify-center ${isBerlin ? "gap-2 [&_button]:size-10 [&_svg]:size-4" : "gap-4"}`}>
              <RoundBtn label={mic ? "Mute microphone" : "Turn on microphone"} active={mic} onClick={toggleMic}>{mic ? <Mic /> : <MicOff />}</RoundBtn>
              <RoundBtn label={cam ? "Turn camera off" : "Turn camera on"} active={cam} onClick={toggleCam}>{cam ? <Video /> : <VideoOff />}</RoundBtn>
              <Button variant="ghost" onClick={() => { setVideo(false); setMic(false); setCam(false); }} aria-label="End video"
                className="grid size-16 place-items-center rounded-full bg-destructive text-destructive-foreground shadow-float transition hover:brightness-110 active:scale-95">
                <PhoneOff className="size-7" />
              </Button>
            </div>
          </section>
        </Collapsible>

        {/* Chat column */}
        <Collapsible open={chatOpen} onOpen={() => setChatOpen(true)} label="Conversation" icon={<MessageCircle className="size-4" />}
          openClass={`flex-1 ${isBerlin ? `min-h-[52dvh] lg:min-h-0 lg:min-w-[280px] ${website ? "lg:max-w-[340px]" : ""}` : video ? "lg:max-w-[480px]" : ""}`}
          barClass="h-11 lg:h-auto lg:w-11">
          <section aria-label="Conversation" className="flex h-full min-h-0 w-full flex-col">
            <header className={`glass flex items-center gap-3 border-x-0 border-t-0 px-4 py-3 ${video && !isBerlin ? "lg:flex hidden" : ""}`}>
              <Button variant="ghost" onClick={onBack} aria-label="Back" className="grid size-12 shrink-0 place-items-center rounded-full hover:bg-card lg:hidden"><ArrowLeft /></Button>
              <img src={c.photo} alt="" className="size-12 shrink-0 rounded-full object-cover" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-lg font-semibold">{c.name}</p>
                <p className="truncate text-sm text-muted-foreground">{title}</p>
              </div>
              <CollapseButton label="Conversation" onClick={() => setChatOpen(false)} className="hidden lg:grid" />
              {!video && (
                <Button variant="ghost" onClick={() => setVideo(true)} className="inline-flex h-12 shrink-0 items-center gap-2 rounded-full bg-primary px-5 font-semibold text-primary-foreground shadow-float transition hover:brightness-110">
                  <Video className="size-5" /> <span className="hidden sm:inline">Video</span>
                </Button>
              )}
            </header>

            <div className={`flex-1 overflow-y-auto px-4 py-6 ${video ? "" : "lg:px-10"}`}>
              <div className={`mx-auto flex flex-col gap-4 ${video ? "" : "max-w-3xl"}`}>
                {msgs.map((m) => <Bubble key={m.id} m={m} photo={c.photo} />)}
                {typing && (
                  <div className="flex items-end gap-2">
                    <img src={c.photo} alt="" className="size-9 rounded-full object-cover" />
                    <div className="glass-strong flex gap-1.5 rounded-3xl rounded-bl-md px-5 py-4">
                      {[0, 1, 2].map((i) => <span key={i} className="size-2.5 animate-bounce rounded-full bg-muted-foreground" style={{ animationDelay: `${i * 150}ms` }} />)}
                    </div>
                  </div>
                )}
                <div ref={endRef} />
              </div>
            </div>

            {notice && (
              <div role="status" className="glass-strong animate-rise mx-4 mb-2 rounded-2xl px-5 py-3 text-base shadow-soft">{notice}</div>
            )}

            {/* Composer */}
            <div className="px-3 pb-4 pt-1 lg:px-6">
              <div className={`mx-auto ${video ? "" : "max-w-3xl"}`}>
                {voice ? (
                  <div className="glass-strong flex items-center gap-4 rounded-[2rem] p-3 shadow-soft">
                    <span className="relative grid size-16 shrink-0 place-items-center">
                      <span className="animate-breathe absolute inset-0 rounded-full bg-accent" />
                      <span className="relative grid size-14 place-items-center rounded-full bg-primary text-primary-foreground"><Mic /></span>
                    </span>
                    <p className="min-w-0 flex-1 text-lg">Voice is coming soon. Type for now.</p>
                    <Button variant="ghost" onClick={() => { setVoice(false); inputRef.current?.focus(); }} aria-label="Switch to typing" className="grid size-14 shrink-0 place-items-center rounded-full hover:bg-muted"><Keyboard /></Button>
                  </div>
                ) : (
                  <form onSubmit={(e) => { e.preventDefault(); send(text); }} className="glass-strong flex items-end gap-2 rounded-[2rem] p-2 shadow-soft">
                    <Button variant="ghost" type="button" onClick={() => fileRef.current?.click()} aria-label="Add a photo or document" className="grid size-10 shrink-0 place-items-center rounded-full text-muted-foreground hover:bg-muted hover:text-foreground"><Paperclip /></Button>
                    <input ref={fileRef} type="file" accept="image/*,.pdf,.doc,.docx" className="hidden"
                      onChange={(e) => { const f = e.target.files?.[0]; if (f) send("", f.name); e.target.value = ""; }} />
                    <textarea
                      ref={inputRef} value={text} rows={1} aria-label="Message"
                      onChange={(e) => setText(e.target.value)}
                      onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(text); } }}
                      placeholder={`Message ${c.name}…`}
                      className="max-h-40 min-h-14 min-w-0 flex-1 resize-none bg-transparent py-4 text-lg outline-none placeholder:text-muted-foreground"
                    />
                    {text.trim() ? (
                      <Button variant="ghost" type="submit" aria-label="Send" className="grid size-10 shrink-0 place-items-center rounded-full bg-primary text-primary-foreground shadow-float transition active:scale-95"><ArrowUp className="size-7" /></Button>
                    ) : (
                      <Button variant="ghost" type="button" onClick={() => setVoice(true)} aria-label="Talk instead" className="grid size-10 shrink-0 place-items-center rounded-full bg-secondary text-secondary-foreground transition hover:bg-accent"><Mic /></Button>
                    )}
                  </form>
                )}
              </div>
            </div>
          </section>
        </Collapsible>

        {isBerlin && (
          <Collapsible open={website} onOpen={() => setWebsite(true)} label="Website guide" icon={<Globe className="size-4" />}
            openClass="min-h-[75dvh] flex-1 lg:min-h-0" barClass="h-11 lg:h-auto lg:w-11">
            <div className="flex h-full min-h-0 w-full flex-col">
              <div className="flex justify-end p-1">
                <CollapseButton label="Website guide" onClick={() => setWebsite(false)} />
              </div>
              <BerlinGuide onStep={(message) => setMsgs((m) => [...m, { id: Date.now(), from: "ai", text: message }])} />
            </div>
          </Collapsible>
        )}
        {!chatOpen && !video && !website && <div className="grid flex-1 place-items-center"><Button onClick={() => setChatOpen(true)}><MessageCircle /> Open conversation</Button></div>}
      </div>
      </div>
    </div>
  );
}

function CollapseButton({ label, onClick, className = "" }: { label: string; onClick: () => void; className?: string }) {
  return (
    <Button variant="ghost" size="icon" onClick={onClick} aria-label={`Collapse ${label}`} title={`Collapse ${label}`}
      className={`size-8 shrink-0 rounded-full text-muted-foreground hover:text-foreground ${className}`}>
      <ArrowLeft className="size-4 rotate-0 lg:-rotate-90" />
    </Button>
  );
}

function Collapsible({
  open, onOpen, label, icon, className = "", openClass, barClass, children,
}: {
  open: boolean; onOpen: () => void; label: string; icon: React.ReactNode;
  className?: string; openClass: string; barClass: string; children: React.ReactNode;
}) {
  return (
    <div
      aria-label={label}
      className={`relative shrink-0 overflow-hidden transition-all duration-300 ease-in-out ${className} ${open ? openClass : barClass}`}
    >
      {/* Expanded content: fades in once open */}
      <div className={`h-full w-full transition-opacity duration-300 ${open ? "opacity-100 delay-150" : "pointer-events-none absolute inset-0 opacity-0"}`} aria-hidden={!open}>
        {open ? children : null}
      </div>
      {/* Collapsed bar: click to expand */}
      {!open && (
        <button
          type="button"
          onClick={onOpen}
          aria-label={`Expand ${label}`}
          title={`Expand ${label}`}
          className="glass flex h-full w-full animate-in fade-in duration-300 items-center justify-center gap-2 rounded-lg px-3 text-muted-foreground transition hover:text-foreground lg:flex-col lg:px-0 lg:py-3"
        >
          {icon}
          <span className="whitespace-nowrap text-xs font-semibold lg:[writing-mode:vertical-rl]">{label}</span>
        </button>
      )}
    </div>
  );
}

function RoundBtn({ children, label, active, onClick }: { children: React.ReactNode; label: string; active: boolean; onClick: () => void }) {
  return (
    <Button variant="ghost" onClick={onClick} aria-label={label} aria-pressed={active}
      className={`grid size-16 place-items-center rounded-full shadow-float transition active:scale-95 ${active ? "bg-card text-foreground" : "glass-dark"}`}>
      {children}
    </Button>
  );
}

function Bubble({ m, photo }: { m: Msg; photo: string }) {
  if (m.from === "me")
    return (
      <div className="animate-rise ml-auto max-w-[85%] rounded-3xl rounded-br-md bg-bubble-user px-5 py-3.5 text-lg leading-relaxed text-bubble-user-foreground shadow-float">
        {m.file && <span className="mb-1 flex items-center gap-2 font-semibold"><FileText className="size-5" />{m.file}</span>}
        {m.text}
      </div>
    );
  return (
    <div className="animate-rise flex max-w-[90%] items-end gap-2">
      <img src={photo} alt="" className="size-9 shrink-0 rounded-full object-cover" />
      <div className="glass-strong rounded-3xl rounded-bl-md px-5 py-3.5 text-lg leading-relaxed">{m.text}</div>
    </div>
  );
}
