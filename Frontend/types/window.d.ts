// Extend the Window interface to include our custom properties
declare interface Window {
  setAirShoppingResponse: (data: any) => void;
  airShoppingResponseData: any;
}
