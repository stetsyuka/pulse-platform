import "./globals.css";

export const metadata = { title: "Pulse Platform" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="uk">
      <body className="bg-slate-50 text-slate-900">{children}</body>
    </html>
  );
}
