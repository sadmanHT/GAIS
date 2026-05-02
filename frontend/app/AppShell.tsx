"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/", label: "Today" },
  { href: "/plan", label: "Plan" },
  { href: "/study", label: "Study" },
  { href: "/progress", label: "Progress" },
  { href: "/diagnostic", label: "Insights" },
  { href: "/test", label: "Mock Test" },
  { href: "/onboard", label: "Onboarding" },
  { href: "/settings", label: "Settings" },
];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const fullBleed = pathname === "/study" || pathname === "/test" || pathname === "/onboard";

  return (
    <div className={fullBleed ? "study-root" : "shell"}>
      {!fullBleed ? (
        <aside className="side">
          <div>
            <Link href="/" className="brand">
              gais
            </Link>
            <div className="brand-sub">est. 2026</div>
          </div>
          <nav className="nav">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`nav-item ${pathname === item.href ? "on" : ""}`}
              >
                {item.label}
              </Link>
            ))}
          </nav>
          <div className="side-foot">
            <div className="side-user">
              <div className="av">M</div>
              <div>
                <b>Mei Aoki</b>
                <span>Day 12 - target 332</span>
              </div>
            </div>
          </div>
        </aside>
      ) : null}
      <div className="main">{children}</div>
    </div>
  );
}
