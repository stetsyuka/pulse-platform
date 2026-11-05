import type { Order } from "contracts";
import { formatCents } from "@/lib/money";
import { log } from "@/lib/logger";

const API_URL = process.env.API_URL ?? "http://localhost:8001";

async function fetchOrders(): Promise<Order[]> {
  try {
    const resp = await fetch(`${API_URL}/orders?limit=20`, { cache: "no-store" });
    if (!resp.ok) throw new Error(`API ${resp.status}`);
    return (await resp.json()) as Order[];
  } catch (e) {
    log("error", "failed to load orders", { error: String(e) });
    return [];
  }
}

export default async function OrdersPage() {
  const orders = await fetchOrders();
  return (
    <main className="mx-auto max-w-3xl p-8">
      <h1 className="mb-6 text-2xl font-semibold">Замовлення</h1>
      {orders.length === 0 ? (
        <p className="text-slate-500">Замовлень поки немає або API недоступний.</p>
      ) : (
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b">
              <th className="py-2">#</th>
              <th>Клієнт</th>
              <th>Сума</th>
              <th>Знижка</th>
              <th>Статус</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((o) => (
              <tr key={o.id} className="border-b last:border-0">
                <td className="py-2">{o.id}</td>
                <td>{o.customer_id}</td>
                <td>{formatCents(o.subtotal_cents)}</td>
                <td>{formatCents(o.discount_cents)}</td>
                <td>{o.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
