import { useState } from "react";
import { Activity, Menu, X, ChevronRight, User as UserIcon, LogOut } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { AuthModal } from "@/components/auth/AuthModal";

interface NavbarProps {
  currentRoute?: string;
}

export function Navbar({ currentRoute }: NavbarProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState<"signin" | "signup">("signin");
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);

  const { user, signOut, userProfile } = useAuth();
  const isDarkFont = currentRoute === "prediction" || currentRoute === "cdss";

  const navLinks = [
    { label: "Home", href: "#hero", route: "landing" },
    { label: "Live AQI", href: "#dashboard", route: "dashboard" },
    { label: "Prediction", href: "#prediction", route: "prediction" },
    { label: "Health Risk", href: "#cdss", route: "cdss" },
    { label: "GIS Map", href: "#gis", route: "gis" },
    { label: "About", href: "#about", route: "about" },
  ];

  const handleOpenAuth = (mode: "signin" | "signup") => {
    setAuthMode(mode);
    setAuthModalOpen(true);
    setMobileMenuOpen(false);
  };

  return (
    <>
      <header className="absolute top-0 left-0 right-0 z-50 w-full bg-transparent">
        <nav
          aria-label="Main Navigation"
          className="mx-auto flex w-full max-w-7xl items-center justify-between px-4 py-4 md:px-8"
        >
          {/* Brand Logo */}
          <a
            href="#"
            className="flex items-center gap-2.5 group focus:outline-none focus:ring-2 focus:ring-white/50 rounded-lg p-1"
          >
            <div className={`flex h-8 w-8 items-center justify-center rounded-lg shadow-sm transition group-hover:scale-105 ${
              isDarkFont ? "bg-slate-950 text-white" : "bg-white/90 text-sky-800 group-hover:bg-white"
            }`}>
              <Activity className="h-5 w-5 stroke-[2.5]" />
            </div>
            <div className="flex flex-col">
              <span className={`text-xl font-bold tracking-tight drop-shadow-md ${
                isDarkFont ? "text-slate-950" : "text-white"
              }`}>
                AI-AQI
              </span>
            </div>
          </a>

          {/* Desktop Navigation Links */}
          <div className="hidden items-center gap-8 text-sm font-medium md:flex">
            {navLinks.map((link) => {
              const isActive = currentRoute === link.route;
              return (
                <a
                  key={link.label}
                  href={link.href}
                  className={`relative transition focus:outline-none after:absolute after:bottom-0 after:left-0 after:h-[2px] after:transition-all ${
                    isDarkFont
                      ? isActive
                        ? "text-slate-950 font-bold after:bg-slate-950 after:w-full"
                        : "text-slate-800 hover:text-slate-950 after:bg-slate-950 after:w-0 hover:after:w-full"
                      : isActive
                        ? "text-white font-semibold after:bg-white after:w-full"
                        : "text-white/80 hover:text-white after:bg-white after:w-0 hover:after:w-full"
                  }`}
                >
                  {link.label}
                </a>
              );
            })}
          </div>

          {/* Action Buttons & Auth (Desktop) */}
          <div className="hidden items-center gap-3.5 sm:flex">
            {user ? (
              <div className="relative">
                <button
                  onClick={() => setUserDropdownOpen(!userDropdownOpen)}
                  className={`flex items-center gap-2 rounded-full border px-3.5 py-1.5 text-xs font-semibold backdrop-blur-md transition ${
                    isDarkFont
                      ? "border-slate-900/30 bg-slate-900/10 text-slate-900 hover:bg-slate-900/20"
                      : "border-white/30 bg-white/15 text-white hover:bg-white/25"
                  }`}
                >
                  <UserIcon className={`h-3.5 w-3.5 ${isDarkFont ? "text-slate-700" : "text-sky-200"}`} />
                  <span>{userProfile?.full_name || user.email?.split("@")[0]}</span>
                  <span className={`rounded px-1.5 py-0.5 text-[10px] uppercase font-bold ${
                    isDarkFont ? "bg-slate-900 text-white" : "bg-sky-500/30 text-sky-200"
                  }`}>
                    {userProfile?.role || "Patient"}
                  </span>
                </button>

                {/* User Dropdown */}
                {userDropdownOpen && (
                  <div className="absolute right-0 mt-2 w-48 rounded-xl border border-white/20 bg-slate-900/95 p-2 shadow-2xl backdrop-blur-xl text-xs text-white">
                    <div className="border-b border-white/10 px-3 py-2">
                      <p className="font-semibold text-white">{userProfile?.full_name || "User Account"}</p>
                      <p className="truncate text-slate-400 text-[11px]">{user.email}</p>
                    </div>
                    <button
                      onClick={() => { signOut(); setUserDropdownOpen(false); }}
                      className="mt-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-rose-300 hover:bg-rose-500/20 transition-colors"
                    >
                      <LogOut className="h-3.5 w-3.5" />
                      <span>Sign Out</span>
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <>
                <button
                  onClick={() => handleOpenAuth("signin")}
                  className={`text-sm font-medium transition focus:outline-none focus:ring-1 rounded-full px-3 py-1.5 ${
                    isDarkFont
                      ? "text-slate-900 hover:text-black focus:ring-slate-900/40"
                      : "text-white/90 hover:text-white focus:ring-white/40"
                  }`}
                >
                  Sign In
                </button>
                <button
                  onClick={() => handleOpenAuth("signup")}
                  className={`inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-sm font-semibold shadow-md transition hover:shadow-lg focus:outline-none ${
                    isDarkFont
                      ? "bg-slate-950 text-white hover:bg-slate-900 focus:ring-2 focus:ring-slate-900"
                      : "bg-white text-sky-800 hover:bg-white/90 focus:ring-2 focus:ring-white/60"
                  }`}
                >
                  <span>Join AI-AQI</span>
                  <ChevronRight className="h-4 w-4" />
                </button>
              </>
            )}
          </div>

          {/* Mobile Menu Toggle Button */}
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-expanded={mobileMenuOpen}
            aria-label="Toggle navigation menu"
            className={`flex h-9 w-9 items-center justify-center rounded-lg border backdrop-blur-sm transition md:hidden focus:outline-none focus:ring-2 ${
              isDarkFont
                ? "border-slate-900/30 bg-slate-900/10 text-slate-900 hover:bg-slate-900/20 focus:ring-slate-900"
                : "border-white/30 bg-white/10 text-white hover:bg-white/20 focus:ring-white"
            }`}
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </nav>

        {/* Mobile Menu Dropdown */}
        {mobileMenuOpen && (
          <div className="mx-4 mt-2 rounded-2xl border border-white/30 bg-sky-950/80 p-5 shadow-xl backdrop-blur-md md:hidden animate-in fade-in slide-in-from-top-2 duration-200">
            <div className="flex flex-col space-y-3">
              {navLinks.map((link) => (
                <a
                  key={link.label}
                  href={link.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className="rounded-lg px-3 py-2 text-sm font-medium text-white/90 transition hover:bg-white/10 hover:text-white"
                >
                  {link.label}
                </a>
              ))}
              <div className="pt-3 border-t border-white/20 flex flex-col gap-2">
                {user ? (
                  <button
                    onClick={() => { signOut(); setMobileMenuOpen(false); }}
                    className="w-full text-center rounded-xl border border-rose-400/40 bg-rose-500/20 py-2 text-sm font-medium text-rose-200 backdrop-blur-sm"
                  >
                    Sign Out ({user.email?.split("@")[0]})
                  </button>
                ) : (
                  <>
                    <button
                      onClick={() => handleOpenAuth("signin")}
                      className="w-full text-center rounded-xl border border-white/40 bg-white/10 py-2 text-sm font-medium text-white backdrop-blur-sm"
                    >
                      Sign In
                    </button>
                    <button
                      onClick={() => handleOpenAuth("signup")}
                      className="w-full text-center rounded-xl bg-white py-2 text-sm font-semibold text-sky-800 shadow-md"
                    >
                      Join AI-AQI
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        )}
      </header>

      {/* Auth Modal Overlay */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        initialMode={authMode}
      />
    </>
  );
}
