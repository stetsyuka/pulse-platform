// Гроші приходять з API в цілих центах; форматуємо лише на виводі.
export function formatCents(cents: number, currency = "USD"): string {
  return new Intl.NumberFormat("uk-UA", { style: "currency", currency }).format(cents / 100);
}
