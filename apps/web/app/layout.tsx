import "../styles/globals.css";

export const metadata = {
  title: "OpenContractRx",
  description: "Contract intelligence and renewal platform for hospitals",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="container">
          <header className="header">
            <div className="brand">OpenContractRx</div>
            <nav className="nav">
              <a href="/">Home</a>
              <a href="/contracts">Contracts</a>
            </nav>
          </header>
          <main className="main">{children}</main>
          <footer className="footer">Apache-2.0 • Built for on-prem friendly deployments</footer>
        </div>
      </body>
    </html>
  );
}