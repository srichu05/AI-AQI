import { useState, useEffect } from "react";
import { AuthProvider } from "@/context/AuthContext";
import { Navbar } from "@/components/shared/Navbar";
import { LandingPage } from "@/features/landing";
import { DashboardPage } from "@/features/dashboard";
import { PredictionPage } from "@/features/prediction";
import { CDSSPage } from "@/features/cdss";
import { GISPage } from "@/features/gis";
import { AboutPage } from "@/features/about";

export type RouteState = "landing" | "dashboard" | "prediction" | "cdss" | "gis" | "about";

export default function App() {
  const [currentRoute, setCurrentRoute] = useState<RouteState>(() => {
    if (typeof window !== "undefined") {
      const path = window.location.pathname;
      const hash = window.location.hash;
      if (path === "/gis" || hash === "#gis") {
        return "gis";
      }
      if (path === "/cdss" || hash === "#cdss") {
        return "cdss";
      }
      if (path === "/prediction" || hash === "#prediction") {
        return "prediction";
      }
      if (path === "/dashboard" || hash === "#dashboard") {
        return "dashboard";
      }
      if (path === "/about" || hash === "#about") {
        return "about";
      }
    }
    return "landing";
  });

  useEffect(() => {
    const handleLocationChange = () => {
      const path = window.location.pathname;
      const hash = window.location.hash;
      if (path === "/gis" || hash === "#gis") {
        setCurrentRoute("gis");
      } else if (path === "/cdss" || hash === "#cdss") {
        setCurrentRoute("cdss");
      } else if (path === "/prediction" || hash === "#prediction") {
        setCurrentRoute("prediction");
      } else if (path === "/dashboard" || hash === "#dashboard") {
        setCurrentRoute("dashboard");
      } else if (path === "/about" || hash === "#about") {
        setCurrentRoute("about");
      } else {
        setCurrentRoute("landing");
      }
    };

    window.addEventListener("popstate", handleLocationChange);
    window.addEventListener("hashchange", handleLocationChange);
    return () => {
      window.removeEventListener("popstate", handleLocationChange);
      window.removeEventListener("hashchange", handleLocationChange);
    };
  }, []);

  const navigateToLanding = () => {
    window.location.hash = "";
    if (
      window.location.pathname === "/dashboard" ||
      window.location.pathname === "/prediction" ||
      window.location.pathname === "/cdss" ||
      window.location.pathname === "/gis" ||
      window.location.pathname === "/about"
    ) {
      window.history.pushState(null, "", "/");
    }
    setCurrentRoute("landing");
  };

  return (
    <AuthProvider>
      <div className="relative min-h-screen w-full">
        <Navbar currentRoute={currentRoute} />
        <main className="w-full">
          {currentRoute === "gis" ? (
            <GISPage />
          ) : currentRoute === "cdss" ? (
            <CDSSPage />
          ) : currentRoute === "prediction" ? (
            <PredictionPage />
          ) : currentRoute === "dashboard" ? (
            <DashboardPage onBackToLanding={navigateToLanding} />
          ) : currentRoute === "about" ? (
            <AboutPage />
          ) : (
            <LandingPage />
          )}
        </main>
      </div>
    </AuthProvider>
  );
}

