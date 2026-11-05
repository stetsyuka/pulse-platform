// Типи контрактів API. Джерело правди — OpenAPI бекенду (`pnpm generate:types`).
// Не редагуйте згенерований openapi.d.ts вручну; тут — лише зручні реекспорти.
export interface Order {
  id: number;
  customer_id: string;
  subtotal_cents: number;
  discount_cents: number;
  status: string;
  created_at: string;
}
