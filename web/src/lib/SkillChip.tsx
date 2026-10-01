import { skillTier } from "@/lib/skillTier";
import { SKILL_FLAG_MARK, type SkillFlag } from "@/types";

interface SkillChipProps {
  value: number;
  title?: string;
  flag?: SkillFlag;
}

export function SkillChip({ value, title, flag }: SkillChipProps) {
  const tier = skillTier(value);
  return (
    <div
      className="w-full h-6 rounded flex items-center justify-center text-[10px] font-bold text-white"
      style={{ backgroundColor: tier.bg }}
      title={title ?? `${value} — ${tier.label}`}
    >
      {value}
      {flag && <span className="ml-0.5 text-[8px]">{SKILL_FLAG_MARK[flag]}</span>}
    </div>
  );
}
