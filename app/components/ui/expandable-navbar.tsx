"use client";

import * as React from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useOnClickOutside } from "usehooks-ts";
import { cn } from "../../lib/utils";
import { LucideIcon } from "lucide-react";
import { throttle } from 'lodash';

interface NavItem {
  title: string;
  icon: LucideIcon;
  link: string;
}

interface ExpandableNavbarProps {
  items: NavItem[];
  className?: string;
  activeColor?: string;
}

const buttonVariants = {
  initial: {
    gap: 0,
  },
  animate: (isSelected: boolean) => ({
    gap: isSelected ? ".5rem" : 0,
  }),
};

const spanVariants = {
  initial: { width: 0, opacity: 0 },
  animate: { width: "auto", opacity: 1 },
  exit: { width: 0, opacity: 0 },
};

const transition = { delay: 0.1, type: "spring", bounce: 0, duration: 0.6 };

export function ExpandableNavbar({
  items,
  className,
  activeColor = "text-white",
}: ExpandableNavbarProps) {
  const [selected, setSelected] = React.useState<number | null>(null);
  const [isScrolled, setIsScrolled] = React.useState(false);
  const [activeSection, setActiveSection] = React.useState<string>("rankings");
  const outsideClickRef = React.useRef(null);

  useOnClickOutside(outsideClickRef, () => {
    setSelected(null);
  });

  React.useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);

      // Update active section based on scroll position
      const sections = ["rankings", "search", "features", "about"];
      const sectionElements = sections.map(id => document.getElementById(id));
      const scrollPosition = window.scrollY + window.innerHeight / 2;

      for (let i = sectionElements.length - 1; i >= 0; i--) {
        const section = sectionElements[i];
        if (section && section.offsetTop <= scrollPosition) {
          setActiveSection(sections[i]);
          break;
        }
      }
    };

    const throttledHandleScroll = throttle(handleScroll, 100);
    window.addEventListener("scroll", throttledHandleScroll);
    return () => window.removeEventListener("scroll", throttledHandleScroll);
  }, []);

  const handleNavClick = (e: React.MouseEvent<HTMLAnchorElement>, sectionId: string) => {
    e.preventDefault();
    const section = document.getElementById(sectionId.replace('#', ''));
    if (section) {
      section.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <motion.div
      ref={outsideClickRef}
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      className={cn(
        "flex max-w-fit fixed top-6 inset-x-0 mx-auto items-center gap-2 rounded-lg bg-gradient-to-r from-blue-500 to-blue-600 p-1 shadow-lg z-[5000]",
        className
      )}
    >
      {items.map((item, index) => {
        const Icon = item.icon;
        const isActive = activeSection === item.link.replace('#', '');
        const shouldExpand = !isScrolled || (isScrolled && isActive);

        return (
          <a
            href={item.link}
            key={item.title}
            onClick={(e) => {
              handleNavClick(e, item.link);
              setSelected(index);
            }}
          >
            <motion.button
              variants={buttonVariants}
              initial={false}
              animate="animate"
              custom={shouldExpand}
              transition={transition}
              className={cn(
                "relative flex items-center rounded-xl px-4 py-2 text-sm font-medium transition-colors duration-300",
                isActive
                  ? cn("text-white font-medium")
                  : "text-white/80 hover:text-white"
              )}
            >
              <Icon size={20} />
              <motion.span
                animate={{
                  width: shouldExpand ? "auto" : 0,
                  opacity: shouldExpand ? 1 : 0,
                  marginLeft: shouldExpand ? "0.5rem" : 0
                }}
                transition={transition}
                className="overflow-hidden whitespace-nowrap"
              >
                {item.title}
              </motion.span>
            </motion.button>
          </a>
        );
      })}
    </motion.div>
  );
} 