export const berlinServiceUrl = "https://service.berlin.de/dienstleistung/120686/";
export const berlinAppointmentUrl = "https://service.berlin.de/terminvereinbarung/termin/all/120686/";

export const berlinSteps = [
  { title: "Check your documents", instruction: "Start with the required documents. Check the official service page for your situation." },
  { title: "Find the appointment link", instruction: "Choose ‘Termin vereinbaren’ for an in-person Anmeldung appointment." },
  { title: "Continue on berlin.de", instruction: "The official site opens in a new tab. Choose an available appointment there; dates and bookings are not live here." },
] as const;

export function nextBerlinStep(step: number) {
  return Math.min(Math.max(step + 1, 0), berlinSteps.length - 1);
}