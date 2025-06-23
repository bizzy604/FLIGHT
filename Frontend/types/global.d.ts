// Extend the Window interface to include our custom properties
declare global {
  interface Window {
    setAirShoppingResponse: (data: any) => void;
    airShoppingResponseData: any;
  }
}

export {}; // This file needs to be a module
