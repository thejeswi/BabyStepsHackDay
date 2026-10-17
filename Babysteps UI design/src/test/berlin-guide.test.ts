import { describe, expect, it } from "vitest";
import { berlinAppointmentUrl, berlinServiceUrl, nextBerlinStep } from "@/lib/berlin-guide";

describe("Berlin guided handoff", () => {
  it("uses the official Anmeldung service and appointment URLs", () => {
    expect(berlinServiceUrl).toBe("https://service.berlin.de/dienstleistung/120686/");
    expect(berlinAppointmentUrl).toBe("https://service.berlin.de/terminvereinbarung/termin/all/120686/");
  });
  it("advances through document and booking guidance without inventing a confirmation step", () => {
    expect(nextBerlinStep(0)).toBe(1);
    expect(nextBerlinStep(1)).toBe(2);
    expect(nextBerlinStep(2)).toBe(2);
  });
});