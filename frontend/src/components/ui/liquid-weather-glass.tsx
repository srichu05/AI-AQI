// @ts-nocheck
'use client';
import React, { useState } from 'react';
import { motion } from 'motion/react';
import { cn } from "@/lib/utils";

interface LiquidGlassCardProps {
  children: React.ReactNode;
  className?: string;
  draggable?: boolean;
  expandable?: boolean;
  width?: string;
  height?: string;
  expandedWidth?: string;
  expandedHeight?: string;
  blurIntensity?: 'sm' | 'md' | 'lg' | 'xl';
  shadowIntensity?: 'none' | 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  borderRadius?: string;
  glowIntensity?: 'none' | 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  showAnimatedBorder?: boolean;
}

export const LiquidGlassCard = ({
  children,
  className = '',
  draggable = true,
  expandable = false,
  width,
  height,
  expandedWidth,
  expandedHeight,
  blurIntensity = 'xl',
  borderRadius = '32px',
  glowIntensity = 'sm',
  shadowIntensity = 'md',
  showAnimatedBorder = true,
  ...props
}: LiquidGlassCardProps) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleToggleExpansion = (e: {
    target: { closest: (arg0: string) => any };
  }) => {
    if (!expandable) return;
    // Don't toggle if clicking on interactive elements
    if (e.target.closest('a, button, input, select, textarea')) return;
    setIsExpanded(!isExpanded);
  };

  const blurClasses = {
    sm: 'backdrop-blur-sm',
    md: 'backdrop-blur-md',
    lg: 'backdrop-blur-lg',
    xl: 'backdrop-blur-xl',
  };

  const shadowStyles = {
    none: 'inset 0 0 0 0 rgba(255, 255, 255, 0)',
    xs: 'inset 1px 1px 1px 0 rgba(255, 255, 255, 0.15), inset -1px -1px 1px 0 rgba(255, 255, 255, 0.15)',
    sm: 'inset 1.5px 1.5px 1.5px 0 rgba(255, 255, 255, 0.18), inset -1.5px -1.5px 1.5px 0 rgba(255, 255, 255, 0.18)',
    md: 'inset 2px 2px 2px 0 rgba(255, 255, 255, 0.22), inset -2px -2px 2px 0 rgba(255, 255, 255, 0.22)',
    lg: 'inset 2.5px 2.5px 2.5px 0 rgba(255, 255, 255, 0.25), inset -2.5px -2.5px 2.5px 0 rgba(255, 255, 255, 0.25)',
    xl: 'inset 3px 3px 3px 0 rgba(255, 255, 255, 0.28), inset -3px -3px 3px 0 rgba(255, 255, 255, 0.28)',
    '2xl':
      'inset 4px 4px 4px 0 rgba(255, 255, 255, 0.3), inset -4px -4px 4px 0 rgba(255, 255, 255, 0.3)',
  };

  const glowStyles = {
    none: '0 4px 4px rgba(0, 0, 0, 0.05), 0 0 12px rgba(0, 0, 0, 0.05)',
    xs: '0 4px 4px rgba(0, 0, 0, 0.12), 0 0 8px rgba(0, 0, 0, 0.05)',
    sm: '0 4px 4px rgba(0, 0, 0, 0.12), 0 0 12px rgba(0, 0, 0, 0.06)',
    md: '0 4px 4px rgba(0, 0, 0, 0.15), 0 0 16px rgba(0, 0, 0, 0.08)',
    lg: '0 4px 4px rgba(0, 0, 0, 0.15), 0 0 20px rgba(0, 0, 0, 0.08)',
    xl: '0 4px 4px rgba(0, 0, 0, 0.15), 0 0 24px rgba(0, 0, 0, 0.1)',
    '2xl':
      '0 4px 4px rgba(0, 0, 0, 0.15), 0 0 30px rgba(0, 0, 0, 0.1)',
  };

  const containerVariants = expandable
    ? {
        collapsed: {
          width: width || 'auto',
          height: height || 'auto',
          transition: {
            duration: 0.4,
            ease: [0.5, 1.5, 0.5, 1],
          },
        },
        expanded: {
          width: expandedWidth || 'auto',
          height: expandedHeight || 'auto',
          transition: {
            duration: 0.4,
            ease: [0.5, 1.5, 0.5, 1],
          },
        },
      }
    : {};

  const MotionComponent = draggable || expandable ? motion.div : 'div';

  const motionProps =
    draggable || expandable
      ? {
          variants: expandable ? containerVariants : undefined,
          animate: expandable
            ? isExpanded
              ? 'expanded'
              : 'collapsed'
            : undefined,
          onClick: expandable ? handleToggleExpansion : undefined,
          drag: draggable,
          dragConstraints: draggable
            ? { left: 0, right: 0, top: 0, bottom: 0 }
            : undefined,
          dragElastic: draggable ? 0.3 : undefined,
          dragTransition: draggable
            ? {
                bounceStiffness: 300,
                bounceDamping: 10,
                power: 0.3,
              }
            : undefined,
          whileDrag: draggable ? { scale: 1.02 } : undefined,
          whileHover: { scale: 1.01 },
          whileTap: { scale: 0.98 },
        }
      : {};

  return (
    <>
      {/* Hidden SVG Filter */}
      <svg className='hidden'>
        <defs>
          <filter
            id='glass-blur'
            x='0'
            y='0'
            width='100%'
            height='100%'
            filterUnits='objectBoundingBox'
          >
            <feTurbulence
              type='fractalNoise'
              baseFrequency='0.003 0.007'
              numOctaves='1'
              result='turbulence'
            />
            <feDisplacementMap
              in='SourceGraphic'
              in2='turbulence'
              scale='10'
              xChannelSelector='R'
              yChannelSelector='G'
            />
          </filter>
        </defs>
      </svg>
      <MotionComponent
        className={cn(
          `group/glasscard relative ${draggable ? 'cursor-grab active:cursor-grabbing' : ''} ${expandable ? 'cursor-pointer' : ''}`,
          className
        )}
        style={{
          borderRadius,
          ...(width && !expandable && { width }),
          ...(height && !expandable && { height }),
        }}
        {...motionProps}
        {...props}
      >
        {/* Bend Layer (Backdrop blur with distortion) */}
        <div
          className={`absolute inset-0 ${blurClasses[blurIntensity]} z-0`}
          style={{
            borderRadius,
            filter: 'url(#glass-blur)',
          }}
        />

        {/* Face Layer (Main shadow and glow) */}
        <div
          className='absolute inset-0 z-10 pointer-events-none'
          style={{
            borderRadius,
            boxShadow: glowStyles[glowIntensity],
          }}
        />

        {/* Edge Layer (Inner highlights & Animated Outer SVG Border Feature) */}
        <div
          className='absolute inset-0 z-20 pointer-events-none overflow-hidden'
          style={{
            borderRadius,
            boxShadow: shadowStyles[shadowIntensity],
          }}
        >
          {showAnimatedBorder && (
            <svg className="absolute inset-0 size-full pointer-events-none z-30" xmlns="http://www.w3.org/2000/svg">
              <line x1="0" y1="0" x2="100%" y2="0" className="stroke-white/40 stroke-[4] transition-transform duration-700 ease-in-out group-hover/glasscard:-translate-x-full group-hover:-translate-x-full" />
              <line x1="0" y1="0" x2="0" y2="100%" className="stroke-white/40 stroke-[4] transition-transform duration-700 ease-in-out group-hover/glasscard:translate-y-full group-hover:translate-y-full" />
              <line x1="0" y1="100%" x2="100%" y2="100%" className="stroke-white/40 stroke-[4] transition-transform duration-700 ease-in-out group-hover/glasscard:translate-x-full group-hover:translate-x-full" />
              <line x1="100%" y1="0" x2="100%" y2="100%" className="stroke-white/40 stroke-[4] transition-transform duration-700 ease-in-out group-hover/glasscard:-translate-y-full group-hover:-translate-y-full" />
            </svg>
          )}
        </div>

        {/* Content */}
        <div className={cn('relative z-30')}>{children}</div>
      </MotionComponent>
    </>
  );
};
