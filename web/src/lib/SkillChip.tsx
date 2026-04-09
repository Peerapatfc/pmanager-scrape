import { skillTier } from "@/lib/skillTier";

interface SkillChipProps {
  value: number;
  title?: string;
}

export function SkillChip({ value, title }: SkillChipProps) {
  const tier = skillTier(value);
  return (
    <div
      className="w-full h-6 rounded flex items-center justify-center text-[10px] font-bold text-white"
      style={{ backgroundColor: tier.bg }}
      title={title ?? `${value} — ${tier.label}`}
    >
      {value}
    </div>
  );
}
