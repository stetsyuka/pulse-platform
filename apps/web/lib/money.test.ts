import { describe, expect, it } from "vitest";
import { formatCents } from "./money";

describe("formatCents", () => {
  it("formats whole cents without float drift", () => {
    expect(formatCents(1999)).toContain("19,99");
  });
});
