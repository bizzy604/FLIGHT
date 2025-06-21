import React from 'react';
import { ShieldCheck, Smartphone } from 'lucide-react';

interface SecurityInfoProps {
  hasTsaPreCheck: boolean;
}

const SecurityInfo: React.FC<SecurityInfoProps> = ({ hasTsaPreCheck }) => {
  if (!hasTsaPreCheck) return null;
  
  return (
    <div className="flex items-center justify-between mt-6">
      <div className="flex items-center gap-2">
        <ShieldCheck className="w-5 h-5" />
        <span className="text-sm font-bold">TSA Pre✓ Clear</span>
      </div>
      <div className="flex items-center gap-2 text-sm">
        <Smartphone className="w-4 h-4" />
        <span>Mobile Pass</span>
      </div>
    </div>
  );
};

export default SecurityInfo;
