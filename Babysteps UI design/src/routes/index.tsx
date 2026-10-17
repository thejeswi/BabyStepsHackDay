import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Welcome, ChooseCompanion, Home } from "@/components/babysteps/Onboarding";
import { Chat } from "@/components/babysteps/Chat";
import { companions, type CompanionId, type TaskId } from "@/lib/companions";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Babysteps — Your AI companion" },
      { name: "description", content: "A little help, whenever you need it. Talk, type, or video chat with a friendly AI companion." },
      { property: "og:title", content: "Babysteps — Your AI companion" },
      { property: "og:description", content: "A little help, whenever you need it. Just talk, type, or ask." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Index,
});

type Step = "welcome" | "choose" | "home" | "chat";

function Index() {
  const [step, setStep] = useState<Step>("welcome");
  const [companion, setCompanion] = useState<CompanionId | null>(null);
  const [task, setTask] = useState<TaskId>("open");
  const [chatKey, setChatKey] = useState(0);
  const active = companion ?? "alex";

  if (step === "welcome") return <Welcome photo={companions.alex.photo} onNext={() => setStep("choose")} />;
  if (step === "choose")
    return <ChooseCompanion value={companion} onChange={setCompanion} onNext={() => setStep("home")} />;
  if (step === "home")
    return <Home companion={active} onSwitch={() => setStep("choose")}
      onPick={(t) => { setTask(t); setChatKey((k) => k + 1); setStep("chat"); }} />;
  return (
    <Chat key={`${chatKey}-${active}`} companion={active} task={task}
      onBack={() => setStep("home")}
      onSwitch={(c) => setCompanion(c)}
      onNewTask={(t) => { setTask(t); setChatKey((k) => k + 1); }} />
  );
}
