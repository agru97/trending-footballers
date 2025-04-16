"use client"

import React from "react"
import { ExpandableNavbar } from "./ui/expandable-navbar"
import { TrendingUp, Search, Star, Info } from "lucide-react"

export function Navigation() {
  const navItems = [
    {
      title: "Rankings",
      link: "#rankings",
      icon: TrendingUp,
    },
    {
      title: "Search",
      link: "#search",
      icon: Search,
    },
    {
      title: "Features",
      link: "#features",
      icon: Star,
    },
    {
      title: "About",
      link: "#about",
      icon: Info,
    },
  ]

  return (
    <div className="relative w-full">
      <ExpandableNavbar items={navItems} />
    </div>
  )
} 