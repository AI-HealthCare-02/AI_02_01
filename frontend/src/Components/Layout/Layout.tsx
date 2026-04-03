import type { ReactNode } from "react";
import Header from "../Header/Header";

interface LayoutProps {
  children: ReactNode;
}

const Layout = ({ children }: LayoutProps) => {
  return (
    <div className="app-shell">
      <Header />
      <main className="app-main">
        <div className="page-container">{children}</div>
      </main>
    </div>
  );
};

export default Layout;