import React, { useState } from "react";
import { cn } from "@/lib/utils";

export interface FaqItem {
  question: string;
  answer: React.ReactNode;
}

export interface FaqAccordionProps extends React.HTMLAttributes<HTMLDivElement> {
  items?: FaqItem[];
  title?: string;
}

export function FaqAccordion({
  items = [],
  title,
  className,
  ...props
}: FaqAccordionProps) {
  const [activeIndex, setActiveIndex] = useState<number | null>(null);

  const toggleItem = (index: number) => {
    setActiveIndex(activeIndex === index ? null : index);
  };

  return (
    <div className={cn("w-full max-w-4xl mx-auto relative font-sans", className)} {...props}>
      {title && (
        <h2 className="text-center font-bold text-2xl md:text-4xl mb-8 text-white drop-shadow-md">
          {title}
        </h2>
      )}

      <ul className="w-full mx-auto list-none p-0 flex flex-col space-y-3">
        {items.map((item, index) => {
          const isActive = activeIndex === index;
          return (
            <li
              key={index}
              className={cn(
                "w-full relative transition-all duration-300 ease-out rounded-2xl overflow-hidden backdrop-blur-md",
                "border border-white/20 shadow-[0_4px_24px_rgba(0,0,0,0.06)]",
                isActive
                  ? "bg-white/[0.12] border-white/40 shadow-[0_12px_32px_rgba(56,189,248,0.15)]"
                  : "bg-white/[0.06] hover:bg-white/[0.10] hover:border-white/30"
              )}
            >
              <button
                type="button"
                className={cn(
                  "flex flex-row items-center justify-start w-full min-h-[64px] py-4.5 px-5 pl-14 md:pl-16 relative cursor-pointer text-left outline-none transition-colors duration-200",
                  "border-l-[4px] md:border-l-[6px]",
                  isActive
                    ? "border-l-cyan-300 text-white font-bold"
                    : "border-l-white/30 text-white/95 hover:border-l-cyan-300/70 hover:text-white font-semibold"
                )}
                onClick={() => toggleItem(index)}
                aria-expanded={isActive}
              >
                {/* Plus / Minus Symbol */}
                <span
                  className={cn(
                    "absolute left-4 md:left-5 top-1/2 -translate-y-1/2 transition-all duration-200 leading-none select-none",
                    isActive
                      ? "text-2xl md:text-3xl font-bold text-cyan-300"
                      : "text-xl md:text-2xl font-semibold text-cyan-200/70 group-hover:text-cyan-200"
                  )}
                >
                  {isActive ? "−" : "+"}
                </span>

                <span className="pr-8 text-base md:text-lg tracking-tight leading-snug">
                  {item.question}
                </span>

                {/* Chevron indicator */}
                <span
                  className={cn(
                    "absolute right-5 md:right-6 block w-2.5 h-2.5 border-t-2 border-r-2 transition-transform duration-300 ease-in-out",
                    isActive
                      ? "rotate-[-45deg] border-cyan-300"
                      : "rotate-[135deg] border-white/50"
                  )}
                />
              </button>

              {/* Accordion Expandable Answer Body */}
              <div
                className={cn(
                  "grid transition-all duration-300 ease-in-out w-full",
                  "border-l-[4px] md:border-l-[6px]",
                  isActive
                    ? "grid-rows-[1fr] border-l-cyan-300"
                    : "grid-rows-[0fr] border-l-transparent"
                )}
              >
                <div className="overflow-hidden">
                  <div className="flex flex-row items-start justify-start w-full px-5 pl-14 md:pl-16 pb-6 pt-1 text-sm md:text-base font-medium text-white/85 leading-relaxed">
                    <span>{item.answer}</span>
                  </div>
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export default FaqAccordion;
