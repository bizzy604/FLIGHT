import React from 'react';
import { Crown, Wifi, Utensils } from 'lucide-react';

interface ClassTagsProps {
  tags: string[];
}

const tagIcons: Record<string, React.ReactNode> = {
  'BUSINESS': <Crown className="w-3 h-3" />,
  'WIFI': <Wifi className="w-3 h-3" />,
  'MEAL': <Utensils className="w-3 h-3" />,
};

const ClassTags: React.FC<ClassTagsProps> = ({ tags }) => {
  return (
    <div className="mt-6 flex gap-2 flex-wrap">
      {tags.map((tag) => (
        <span 
          key={tag}
          className="rounded-full bg-white/20 px-4 py-2 text-xs font-semibold backdrop-blur-sm flex items-center gap-1"
        >
          {tagIcons[tag]}
          {tag}
        </span>
      ))}
    </div>
  );
};

export default ClassTags;
