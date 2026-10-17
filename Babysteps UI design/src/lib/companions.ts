import alex from "@/assets/alex-human.jpg";
import sam from "@/assets/sam-human.jpg";

export type CompanionId = "alex" | "sam";
export const companions = {
  alex: { id: "alex" as const, name: "Alex", tagline: "Warm, friendly, and patient.", photo: alex },
  sam: { id: "sam" as const, name: "Sam", tagline: "Calm, reassuring, and clear.", photo: sam },
};

export type TaskId = "letter" | "message" | "berlin" | "open";
export const tasks: { id: Exclude<TaskId, "open">; title: string; sub: string }[] = [
  { id: "letter", title: "Understand a letter", sub: "Make a confusing letter simple." },
  { id: "message", title: "Check a suspicious message", sub: "Is this message safe?" },
  { id: "berlin", title: "Book your Anmeldung", sub: "A Bürgeramt appointment in Berlin." },
];

export const openers: Record<TaskId, string> = {
  letter: "Happy to help. Take a photo of the letter, or type what it says. I'll explain it in plain words.",
  message: "Good thinking to check first. Paste the message here, or send a screenshot. Don't click any links yet.",
  berlin: "Let's find your Anmeldung appointment in Berlin. Start with marker 1 to check your documents, then we'll find ‘Termin vereinbaren’. We won't book or submit anything for you.",
  open: "Hi, it's lovely to see you. What's on your mind?",
};

const replies: Record<TaskId, string[]> = {
  letter: [
    "Thanks. In short: this letter says a payment is due by the date at the top. Nothing is urgent today.",
    "Would you like me to help you write a short reply?",
  ],
  message: [
    "This looks like a scam. Real banks never ask you to confirm your PIN by text. Please delete it.",
    "If you're worried, call your bank using the number on the back of your card.",
  ],
  berlin: [
    "For Anmeldung, look for ‘Wohnung anmelden’ on Berlin's official service portal. Follow the numbered marker beside us to find the appointment link.",
    "Choose an available appointment on the official site. Bring your identification and Wohnungsgeberbestätigung; check the official page for the documents that apply to you. A booking is only confirmed when the official site confirms it.",
  ],
  open: [
    "That makes sense. Tell me a little more and we'll take it one step at a time.",
    "You're doing great. What would you like to do next?",
  ],
};

export function reply(task: TaskId, turn: number) {
  const list = replies[task];
  return list[Math.min(turn, list.length - 1)] ?? "";
}
