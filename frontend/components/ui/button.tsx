import * as React from "react";
import { cn } from "@/lib/utils";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "ghost" | "outline" | "danger";
  size?: "sm" | "md" | "icon";
};

export function Button({ className, variant = "primary", size = "md", ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-md border transition disabled:cursor-not-allowed disabled:opacity-50",
        size === "sm" && "h-8 px-3 text-sm",
        size === "md" && "h-10 px-4 text-sm",
        size === "icon" && "h-9 w-9",
        variant === "primary" && "border-[#2f81f7] bg-[#2f81f7] text-white hover:bg-[#1f6feb]",
        variant === "ghost" && "border-transparent bg-transparent text-[#e6edf3] hover:bg-[#21262d]",
        variant === "outline" && "border-[#30363d] bg-[#151b23] text-[#e6edf3] hover:bg-[#21262d]",
        variant === "danger" && "border-[#f85149] bg-[#f85149] text-white hover:bg-[#da3633]",
        className
      )}
      {...props}
    />
  );
}
