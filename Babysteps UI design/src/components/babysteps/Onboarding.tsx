import { Check, ArrowRight, MessageCircle, FileText, ShieldCheck, Landmark } from "lucide-react";
import { companions, tasks, type CompanionId, type TaskId } from "@/lib/companions";

const btn =
  "inline-flex h-16 items-center justify-center gap-3 rounded-full bg-primary px-10 text-lg font-semibold text-primary-foreground shadow-float transition hover:brightness-110 active:scale-[0.98] focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-ring/40 disabled:opacity-40";

export function Welcome({ onNext, photo }: { onNext: () => void; photo: string }) {
  return (
    <main className="relative grid min-h-dvh lg:grid-cols-2">
      <div className="relative h-[52dvh] overflow-hidden lg:order-2 lg:h-dvh">
        <img src={photo} alt="Your companion smiling" className="h-full w-full object-cover" width={1024} height={1280} />
        <div className="absolute inset-x-0 bottom-0 h-40 bg-gradient-to-t from-background to-transparent lg:hidden" />
        <div className="glass-dark absolute left-5 top-5 rounded-full px-4 py-2 text-sm font-medium">Babysteps</div>
      </div>
      <section className="flex flex-col justify-center px-7 pb-12 pt-2 lg:px-20">
        <div className="animate-rise max-w-xl">
          <h1 className="font-display text-5xl leading-[1.05] lg:text-7xl">A little help, whenever you need it.</h1>
          <p className="mt-6 text-xl text-muted-foreground lg:text-2xl">Your personal AI companion. Just talk, type, or ask.</p>
          <button onClick={onNext} className={`${btn} mt-10 w-full sm:w-auto`}>
            Get started <ArrowRight className="size-6" />
          </button>
        </div>
      </section>
    </main>
  );
}

export function ChooseCompanion({
  value, onChange, onNext,
}: { value: CompanionId | null; onChange: (c: CompanionId) => void; onNext: () => void }) {
  return (
    <main className="mx-auto flex min-h-dvh max-w-4xl flex-col px-6 py-10 lg:py-16">
      <h1 className="font-display animate-rise text-4xl lg:text-6xl">Who would you like to talk to?</h1>
      <p className="mt-3 text-xl text-muted-foreground">You can change this anytime.</p>
      <div className="mt-8 grid flex-1 grid-cols-1 gap-5 sm:grid-cols-2">
        {Object.values(companions).map((c, i) => {
          const sel = value === c.id;
          return (
            <button
              key={c.id}
              onClick={() => onChange(c.id)}
              aria-pressed={sel}
              style={{ animationDelay: `${i * 80}ms` }}
              className={`animate-rise group relative aspect-[4/5] max-h-[60dvh] overflow-hidden rounded-[2rem] text-left shadow-soft transition focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-ring/50 ${sel ? "ring-4 ring-primary" : "ring-0"}`}
            >
              <img src={c.photo} alt={c.name} className="h-full w-full object-cover transition duration-700 group-hover:scale-105" width={1024} height={1280} />
              <div className="glass-dark absolute inset-x-3 bottom-3 rounded-3xl p-5">
                <div className="flex items-center justify-between">
                  <span className="font-display text-3xl">{c.name}</span>
                  <span className={`grid size-10 place-items-center rounded-full transition ${sel ? "bg-primary text-primary-foreground" : "border-2 border-on-photo/60"}`}>
                    {sel && <Check className="size-6" />}
                  </span>
                </div>
                <p className="mt-1 text-lg opacity-90">{c.tagline}</p>
              </div>
            </button>
          );
        })}
      </div>
      <button disabled={!value} onClick={onNext} className={`${btn} mt-8 self-stretch sm:self-end`}>
        Continue <ArrowRight className="size-6" />
      </button>
    </main>
  );
}

const icons = { letter: FileText, message: ShieldCheck, berlin: Landmark };

export function Home({ companion, onPick, onSwitch }: { companion: CompanionId; onPick: (t: TaskId) => void; onSwitch: () => void }) {
  const c = companions[companion];
  return (
    <main className="mx-auto flex min-h-dvh max-w-4xl flex-col px-6 py-8 lg:py-16">
      <header className="flex items-center justify-between">
        <button onClick={onSwitch} className="glass flex items-center gap-3 rounded-full py-1.5 pl-1.5 pr-5 text-base font-medium">
          <img src={c.photo} alt="" className="size-11 rounded-full object-cover" />
          {c.name}
          <span className="text-muted-foreground">· Change</span>
        </button>
      </header>
      <h1 className="font-display animate-rise mt-10 text-4xl leading-tight lg:text-6xl">Hi! What can I help you with today?</h1>
      <div className="mt-10 grid gap-4 lg:grid-cols-3">
        {tasks.map((t, i) => {
          const Icon = icons[t.id];
          return (
            <button
              key={t.id}
              onClick={() => onPick(t.id)}
              style={{ animationDelay: `${i * 80}ms` }}
              className="glass-strong animate-rise group flex items-center gap-5 rounded-[1.75rem] p-6 text-left shadow-soft transition hover:-translate-y-1 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-ring/40 lg:flex-col lg:items-start lg:p-8"
            >
              <span className="grid size-16 shrink-0 place-items-center rounded-2xl bg-accent text-accent-foreground">
                <Icon className="size-8" />
              </span>
              <span className="min-w-0">
                <span className="block text-xl font-semibold lg:text-2xl">{t.title}</span>
                <span className="mt-1 block text-lg text-muted-foreground">{t.sub}</span>
              </span>
            </button>
          );
        })}
      </div>
      <button onClick={() => onPick("open")} className="mt-6 inline-flex h-16 items-center justify-center gap-3 rounded-full border-2 border-primary/25 text-lg font-semibold text-primary transition hover:bg-primary/5">
        <MessageCircle className="size-6" /> Just talk to {c.name}
      </button>
    </main>
  );
}
