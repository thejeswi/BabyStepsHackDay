import { useState } from "react";
import { ArrowLeft, ArrowRight, Check, ExternalLink, Globe, LockKeyhole, MapPin } from "lucide-react";
import { Button } from "@/components/ui/button";
import { berlinAppointmentUrl, berlinServiceUrl, berlinSteps, nextBerlinStep } from "@/lib/berlin-guide";

export function BerlinGuide({ onStep }: { onStep: (message: string) => void }) {
  const [step, setStep] = useState(0);
  const [visited, setVisited] = useState(false);
  const current = berlinSteps[step] ?? berlinSteps[0];
  const advance = () => {
    const next = nextBerlinStep(step);
    setStep(next);
    onStep((berlinSteps[next] ?? berlinSteps[0]).instruction);
  };
  return (
    <section aria-label="Berlin Anmeldung guided website" className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden rounded-lg border bg-card">
      <div className="flex flex-wrap items-center gap-2 border-b bg-muted px-4 py-3 text-sm">
        <LockKeyhole className="size-4 text-muted-foreground" />
        <span className="min-w-0 flex-1 break-all text-muted-foreground">service.berlin.de / dienstleistung / 120686</span>
        <Button variant="ghost" size="icon" asChild><a href={berlinServiceUrl} target="_blank" rel="noopener noreferrer" aria-label="Open official Berlin service page" title="Open official Berlin service page"><ExternalLink /></a></Button>
      </div>
      <div className="flex flex-wrap items-center justify-between gap-2 border-b px-5 py-3 text-sm">
        <span className="flex items-center gap-2 font-semibold"><Globe className="size-4" /> Guided preview · not a live website</span>
        <span className="text-muted-foreground">Step {step + 1} of 3</span>
      </div>
      <div className="flex-1 overflow-y-auto">
        <div className="flex items-center justify-between border-b px-6 py-5">
          <span className="text-2xl font-bold">berlin.de</span><span className="text-sm text-muted-foreground">ServicePortal Berlin</span>
        </div>
        <div className="space-y-7 px-6 py-7 lg:px-8">
          <p className="text-sm text-muted-foreground">Bürgeramt / Meldeangelegenheiten</p>
          <h2 className="text-2xl font-semibold leading-tight lg:text-3xl">Wohnsitz – Alleinige Wohnung oder Hauptwohnung anmelden</h2>
          <p className="text-base leading-relaxed text-muted-foreground">Register your main home in Berlin. For an in-person appointment, prepare your documents and continue to the official booking service.</p>
          <div className={`relative border-l-4 p-5 ${step === 0 ? "border-primary bg-secondary" : "border-border"}`}>
            <h3 className="pr-8 text-lg font-semibold">Erforderliche Unterlagen</h3>
            <ul className="mt-3 list-disc space-y-2 pl-5 text-base">
              <li>Identification document</li><li>Wohnungsgeberbestätigung (landlord confirmation)</li><li>Registration form and any additional documents listed for your situation</li>
            </ul>
            {step === 0 && <Marker number={1} label="Documents checked — next step" onClick={advance} />}
            <Button variant="link" asChild className="mt-3 h-auto whitespace-normal p-0"><a href={berlinServiceUrl} target="_blank" rel="noopener noreferrer">Check the full official requirements <ExternalLink /></a></Button>
          </div>
          <div className={`relative border-l-4 p-5 ${step === 1 ? "border-primary bg-secondary" : "border-border"}`}>
            <h3 className="pr-8 text-lg font-semibold">Termin vereinbaren</h3>
            <p className="mb-4 mt-2 text-base text-muted-foreground">Find an appointment at a Berlin Bürgeramt.</p>
            <Button onClick={advance} disabled={step !== 1} className="h-auto min-h-12 whitespace-normal px-5 py-3">Termin vereinbaren <ArrowRight /></Button>
            {step === 1 && <Marker number={2} label="Show where to book your appointment" onClick={advance} />}
          </div>
          {step === 2 && <div className="relative border-l-4 border-primary bg-secondary p-5">
            <h3 className="pr-8 text-lg font-semibold">Ready for the official booking page</h3>
            <p className="mb-4 mt-2 text-base leading-relaxed text-muted-foreground">Choose a location and an available time on berlin.de. If booking is unavailable or under maintenance, try again later. No appointment has been booked here.</p>
            <Button asChild className="h-auto min-h-12 whitespace-normal px-5 py-3"><a href={berlinAppointmentUrl} target="_blank" rel="noopener noreferrer" onClick={() => { setVisited(true); onStep("The booking page opened in a new tab. Pick an available date and time there, then follow its instructions. Only Berlin's confirmation means your appointment is booked."); }}>Open official booking <ExternalLink /></a></Button>
            <span className="absolute right-3 top-3 grid size-8 place-items-center rounded-full bg-primary text-sm font-bold text-primary-foreground">3</span>
            {visited && <p role="status" className="mt-4 flex items-start gap-2 text-sm"><Check className="size-4 shrink-0" /> Booking page opened. Await confirmation on the official site.</p>}
          </div>}
        </div>
      </div>
      <footer className="border-t bg-background p-4">
        <div className="mb-3 flex items-center gap-2 text-sm text-muted-foreground"><MapPin className="size-4" /> {current.title}</div>
        <p className="text-base leading-relaxed">{current.instruction}</p>
        <div className="mt-4 flex items-center justify-between gap-3">
          <Button variant="ghost" disabled={step === 0} onClick={() => setStep((s) => Math.max(0, s - 1))}><ArrowLeft /> Back</Button>
          {step < 2 && <Button onClick={advance}>Next <ArrowRight /></Button>}
          {step === 2 && <Button variant="ghost" onClick={() => { setStep(0); setVisited(false); }}>Restart guide</Button>}
        </div>
      </footer>
    </section>
  );
}

function Marker({ number, label, onClick }: { number: number; label: string; onClick: () => void }) {
  return <Button size="icon" aria-label={label} title={label} onClick={onClick} className="absolute right-3 top-3 size-9 rounded-full ring-4 ring-primary/20">{number}</Button>;
}