import React from 'react';

interface QRCodeProps {
  data: string;
  alt: string;
  caption: string;
}

const QRCode: React.FC<QRCodeProps> = ({ data, alt, caption }) => {
  return (
    <>
      <div className="mt-6 flex justify-center">
        <div className="bg-card p-3 rounded-xl">
          <img 
            src={`https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=${encodeURIComponent(data)}`} 
            alt={alt} 
            className="w-24 h-24" 
          />
        </div>
      </div>
      <div className="mt-4 text-center text-xs opacity-75">
        {caption}
      </div>
    </>
  );
};

export default QRCode;