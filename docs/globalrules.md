Alright, excellent! We have a solid plan. Now, let's transition into the role of a Senior Developer guiding an AI assistant (like yourself, in a way!) to build this Flight Booking Portal.

Here's a comprehensive guide with instructions, best practices, and key concerns:

---

**Project Genesis: Modern Flight Booking Portal with Verteil NDC Integration**

**Objective:**
Develop a sleek, modern, and performant flight booking portal that allows users to search, price, and book flights by integrating with the Verteil NDC API. The frontend will be built with Next.js 15 (App Router) and the backend with Flask.

**Guiding Principles for the AI Assistant (You):**

1.  **User-Centricity:** Every decision must prioritize a smooth, intuitive, and fast user experience.
2.  **Modularity & Reusability:** Build components and services that are well-defined and can be reused.
3.  **Clarity & Maintainability:** Write clean, well-documented code. Follow consistent naming conventions.
4.  **Security First:** Be mindful of data security, especially passenger PII and payment information.
5.  **Performance:** Optimize for speed at every layer (frontend rendering, API response times, database queries).
6.  **Robustness & Error Handling:** Anticipate and gracefully handle potential errors from user input, API calls, and internal processing.
7.  **Testability:** Write code that is easy to test (unit, integration, end-to-end).
8.  **Adherence to NDC Flow:** Strictly follow the multi-step NDC workflow (AirShopping -> FlightPrice -> OrderCreate) as discussed and defined by the Verteil API.

---

**Phase 1: Backend Development (Flask & Verteil Integration)**

**AI Assistant Task 1.1: Setup Flask Backend Core**

*   **Instructions:**
    1.  Initialize a new Flask project (`my_flight_portal_backend`).
    2.  Set up a virtual environment and install necessary base packages: `Flask`, `Flask-CORS`, `requests`, `python-dotenv`.
    3.  Create the basic directory structure: `app.py`, `routes/`, `services/`, `scripts/`, `instance/`.
    4.  Implement `app.py` to initialize Flask, enable CORS (initially permissive for development, to be tightened later), and include a basic health check route (e.g., `/`).
    5.  Store Verteil API credentials and base URL securely (e.g., using `.env` file loaded into `app.config` or `instance/config.py`). **Never commit secrets to the repository.**
*   **Key Concerns:**
    *   **Security:** Secret management is paramount.
    *   **Scalability:** While Flask is lightweight, consider patterns that allow for future scaling if needed (e.g., Blueprints).

**AI Assistant Task 1.2: Integrate Verteil NDC Request Builders**

*   **Instructions:**
    1.  Place the Python scripts (`build_airshopping_rq.py`, `build_flightprice_rq.py`, `build_ordercreate_rq.py`) into the `scripts/` directory.
    2.  Ensure these scripts are importable and their main functions can be called with appropriate parameters.
    3.  Refactor them slightly if needed to be pure functions that accept all necessary data as arguments and return the request payload dictionary, rather than performing file I/O in their main execution blocks (the `if __name__ == "__main__":` part is for standalone testing).
*   **Key Concerns:**
    *   **Accuracy:** The generated RQs must exactly match Verteil's schema based on our sample files and their documentation.

**AI Assistant Task 1.3: Implement `flight_service.py`**

*   **Instructions:**
    1.  Create `services/flight_service.py`.
    2.  Implement the `_call_verteil_api(endpoint, payload)` helper function to make authenticated POST requests to Verteil. Include robust error handling for HTTP errors, network issues, and JSON decoding errors. Implement reasonable timeouts.
    3.  Implement `process_air_shopping(search_criteria)`:
        *   Takes frontend search criteria.
        *   Calls `build_airshopping_request` from your script.
        *   Calls Verteil AirShopping API via `_call_verteil_api`.
        *   Implements `transform_airshopping_rs_for_frontend(airshopping_rs)` to parse the complex `AirShoppingRS` and convert it into a simplified, frontend-friendly list of flight offers. This transformation must extract:
            *   `OfferID` (Verteil's)
            *   The root `ShoppingResponseID` and `Owner` from `AirShoppingRS`.
            *   Price, currency.
            *   Parsed itinerary details (segments, airlines, departure/arrival times, airports, stops, duration) for each leg by correctly de-referencing `DataLists`.
            *   Basic baggage info (from `DataLists`).
            *   Simplified fare conditions/cabin class (from `DataLists`).
            *   Any `OfferItemIDs` associated with each offer component (needed for `FlightPriceRQ`).
        *   Return the simplified offers and the `ShoppingResponseID`.
    4.  Implement `process_flight_price(price_request_data)`:
        *   `price_request_data` will include the `OfferID` and `ShoppingResponseID` from the `AirShoppingRS`, and crucially, the *context of the original AirShoppingRS* (its `DataLists` and relevant `Metadata`) because `build_flightprice_rq.py` needs it.
        *   Calls `build_flight_price_request` from your script.
        *   Calls Verteil FlightPrice API.
        *   Implements `transform_flightprice_rs_for_frontend(flight_price_rs)`:
            *   Extracts the *new* (confirmed) `OfferID` and *new* `ShoppingResponseID` from `FlightPriceRS`.
            *   Extracts final price, currency, payment time limits.
            *   Extracts the structure of `OfferItemIDs` and their associated `TravelerReferences` (e.g., "T1", "T2") from `FlightPriceRS.PricedFlightOffer[0].OfferPrice`.
            *   Extracts `PTC` and `ObjectKey` for each passenger from `FlightPriceRS.DataLists.AnonymousTravelerList`.
            *   Return all this confirmed data to be used on the frontend passenger details page and for building the `OrderCreateRQ`.
    5.  Implement `process_order_create(order_data)`:
        *   `order_data` will include:
            *   The *full `FlightPriceRS`* (as `generate_order_create_rq.py` needs its `DataLists` and `Metadata`).
            *   Detailed passenger information (names, DOBs, documents) collected from the frontend.
            *   Payment information (including payment gateway token and method details).
        *   Calls `generate_order_create_rq` from your script.
        *   Calls Verteil OrderCreate API.
        *   Implements `transform_order_create_rs_for_frontend(order_create_rs)`:
            *   Extracts PNR/OrderID, ticket numbers, status, and any warnings.
        *   Return confirmation/error details.
*   **Key Concerns:**
    *   **NDC State Management:** The `ShoppingResponseID` chain is critical.
    *   **Data Transformation Logic:** This is complex. Focus on correctly de-referencing IDs from `DataLists` in RS messages. Start with essential fields and add more iteratively.
    *   **Error Propagation:** Ensure errors from Verteil or internal processing are clearly communicated back.
    *   **Verteil API Specifics:** Pay close attention to Verteil's exact endpoint names and authentication scheme.
    *   **Payment Surcharge Logic:** The top-level `Payment.Amount` in `OrderCreateRQ` must be inclusive of any surcharge. Your logic needs to correctly identify surcharge from `FlightPriceRS` and apply it.

**AI Assistant Task 1.4: Implement Flask API Routes (`routes/verteil_flights.py`)**

*   **Instructions:**
    1.  Create the Blueprint and define the POST routes: `/api/verteil/air-shopping`, `/api/verteil/flight-price`, `/api/verteil/order-create`.
    2.  Ensure routes extract JSON data from requests, call the appropriate service functions from `flight_service.py`, and return JSON responses with correct HTTP status codes (200 for success, 400 for bad request/validation, 500 for server errors).
*   **Key Concerns:**
    *   **Input Validation:** Basic validation of incoming request bodies. More detailed validation can be in the service layer.
    *   **Consistent Error Responses:** Standardize error response format.

**AI Assistant Task 1.5: Testing the Backend**

*   **Instructions:**
    1.  Use tools like Postman or `curl` to test each Flask API endpoint.
    2.  For `/air-shopping`, send a JSON payload matching the expected frontend search criteria. Verify the transformed response.
    3.  Manually construct payloads for `/flight-price` (using data from a test `/air-shopping` response) and `/order-create` (using data from a test `/flight-price` response, mock passenger/payment data).
    4.  Verify that the payloads sent to the (mocked or real) Verteil API are correctly structured by logging them from `_call_verteil_api`.
*   **Key Concerns:**
    *   **Data Flow:** Ensure IDs and context are passed correctly between your service functions.
    *   **Mocking Verteil:** For initial development, you might mock the `_call_verteil_api` to return your sample RS files to test the transformation logic without hitting Verteil repeatedly.

---

**Phase 2: Frontend Development (Next.js 15 App Router)**

**AI Assistant Task 2.1: Setup Next.js Project & Core Layout**

*   **Instructions:**
    1.  Initialize Next.js project (if not done).
    2.  Set up Tailwind CSS and any chosen UI component library (e.g., Shadcn/ui).
    3.  Create the root `layout.tsx` and basic `Navbar` and `Footer` components.
    4.  Implement basic routing structure using the App Router (`app/` directory) for main pages (Homepage, Search, Results, etc.).
*   **Key Concerns:**
    *   **Responsive Design:** Ensure layout and components are mobile-first.

**AI Assistant Task 2.2: Implement Flight Search UI & Logic**

*   **Instructions:**
    1.  Create `app/(booking)/search/page.tsx` and `FlightSearchForm.tsx` client component.
    2.  Use `react-hook-form` and `zod` for form state management and validation.
    3.  Inputs: Origin, Destination, Dates (use a good date picker like `react-day-picker`), Passenger Counts, Trip Type (One-Way, Round-Trip, Multi-City).
    4.  On submit, construct URL query parameters and navigate to the `/results` page using `next/navigation`'s `useRouter`.
*   **Key Concerns:**
    *   **UX:** Intuitive date selection, clear error messages, responsive form.
    *   **Accessibility:** Proper labels, ARIA attributes.

**AI Assistant Task 2.3: Implement Flight Results Page**

*   **Instructions:**
    1.  Create `app/(booking)/results/page.tsx` as a Server Component.
    2.  Read search parameters from `searchParams`.
    3.  **Data Fetching:**
        *   **Option A (Server Action):** Create a Server Action in `lib/actions.ts` that internally calls the Flask `/api/verteil/air-shopping` endpoint. The page component awaits this action.
        *   **Option B (Direct API Route Call):** The page component can directly `fetch` from your Flask `/api/verteil/air-shopping` endpoint (ensure `NEXT_PUBLIC_FLASK_API_BASE_URL` is set).
    4.  Display loading states (e.g., using Suspense if fetching is done in child components).
    5.  Render `FlightOfferCard.tsx` for each offer received from the Flask backend.
    6.  Implement basic client-side `Filters.tsx` and `SortOptions.tsx` components (can be enhanced later).
*   **Key Concerns:**
    *   **Performance:** Efficient data fetching and rendering, especially for many offers.
    *   **Clarity of Information:** Each `FlightOfferCard` must clearly display essential flight details and price.
    *   **Error Handling:** Gracefully display errors if the API call fails.

**AI Assistant Task 2.4: Implement Offer Selection & Flight Pricing Flow**

*   **Instructions:**
    1.  In `FlightOfferCard.tsx`, the "Select Flight" button should:
        *   Trigger a Server Action (preferred for mutations/data fetching tied to user action).
        *   This Server Action takes the selected `OfferID` and the `ShoppingResponseID` (from the `AirShoppingRS` context, which needs to be available).
        *   The Server Action then `fetch`es your Flask `/api/verteil/flight-price` endpoint, passing:
            *   The `OfferID` and `ShoppingResponseID` from `AirShoppingRS`.
            *   The *context of the original `AirShoppingRS`* (or a snapshot of its `DataLists` and `Metadata` if the full ASRS is too large to pass). This is crucial because `build_flightprice_rq.py` needs this.
        *   The Flask API returns the confirmed offer details from `FlightPriceRS` (new `OfferID`, new `ShoppingResponseID`, price, time limits, passenger PTC/ObjectKey structure).
        *   The Server Action, upon success, redirects the user to `/passenger-details`, passing these confirmed details via query parameters or by temporarily storing them (e.g., in a short-lived server-side session or encrypted cookie if small enough, or a temporary DB record).
*   **Key Concerns:**
    *   **State Management:** Passing the correct `OfferID` and `ShoppingResponseID` from the AirShopping step to the FlightPricing step.
    *   **Passing ASRS Context:** Deciding how to provide the `build_flightprice_rq.py` script (running in Flask) with the necessary `AirShoppingRS` data. Sending the whole ASRS from Next.js to Flask for each price call might be inefficient if large. Caching ASRS on the Flask side keyed by `ShoppingResponseID` is a more advanced but better solution.
    *   **User Feedback:** Provide loading indicators during the FlightPrice call.

**AI Assistant Task 2.5: Implement Passenger Details Page & Form**

*   **Instructions:**
    1.  Create `app/(booking)/passenger-details/page.tsx`.
    2.  It receives/fetches the confirmed offer details (from the FlightPricing step).
    3.  Display the final price and payment time limit prominently.
    4.  Implement `PassengerForm.tsx` using `react-hook-form` and `zod`.
        *   Dynamically render form fields for each passenger based on `passengerPTCs` (from `FlightPriceRS` context).
        *   Include fields for Title, Given Name(s), Surname, DOB, Gender.
        *   Include fields for `PassengerDocument` (Type, ID, Expiry, Issuance Country, etc.).
        *   Contact fields (Email, Phone) for the lead passenger.
        *   Handle infant association.
    5.  On submit, the form should:
        *   Gather all passenger data.
        *   Temporarily store this data along with the confirmed offer context (`OfferID` and `ShoppingResponseID` from `FlightPriceRS`, and potentially the full `FlightPriceRS`) – e.g., using `sessionStorage` (simple for client-side only state) or a more robust method like a short-lived database entry or POSTing to a staging API endpoint on Flask.
        *   Redirect to the `/payment` page.
*   **Key Concerns:**
    *   **Data Validation:** Thorough client-side and server-side validation of passenger details.
    *   **UX for Multiple Passengers:** Easy-to-use form for multiple travelers.
    *   **Security of PII:** While client-side, be mindful of how data is handled before secure submission.
    *   **Document Validation:** Basic validation for document fields (e.g., date formats).

**AI Assistant Task 2.6: Implement Payment Page & Logic**

*   **Instructions:**
    1.  Create `app/(booking)/payment/page.tsx`.
    2.  Retrieve the staged booking data (passenger info, confirmed offer context from `FlightPriceRS`).
    3.  Implement `PaymentForm.tsx`.
    4.  **Integrate Payment Gateway:**
        *   Use the chosen gateway's React components (e.g., Stripe Elements) for secure card input.
        *   Obtain a payment token from the gateway upon successful card validation.
    5.  On "Pay Now" / "Confirm Booking":
        *   Call the `handleCreateOrder` Server Action.
        *   Pass to the Server Action:
            *   All collected passenger data.
            *   The confirmed offer context: `OfferID` and `ShoppingResponseID` from `FlightPriceRS`.
            *   The *full `FlightPriceRS` data* (because `generate_order_create_rq.py` needs it for `DataLists` and `Metadata`).
            *   Payment information:
                *   `MethodType`: "PaymentCard" (or other type)
                *   `Details`: Containing the payment gateway token, card type (VI, MC), etc., structured as required by your `process_payments_for_order_create` function.
                *   `Amount`: The total order amount (inclusive of surcharge).
                *   `Currency`.
                *   `OrderTotalBeforeSurcharge` and `Surcharge` details (if applicable).
*   **Key Concerns:**
    *   **PCI Compliance:** Secure handling of payment information by using the payment gateway's SDKs/Elements. Never let raw card details touch your Next.js server or Flask server if possible.
    *   **Error Handling:** Handle payment gateway errors and API errors robustly.
    *   **Passing Full `FlightPriceRS` Context:** Decide how the `handleCreateOrder` Server Action gets access to the full `FlightPriceRS` needed by the Flask backend. (Option A: Pass from client. Option B: Server Action fetches it from Flask based on an ID if Flask cached it).

**AI Assistant Task 2.7: Implement `handleCreateOrder` Server Action**

*   **Instructions:**
    1.  In `lib/actions.ts`, implement `handleCreateOrder`.
    2.  This action receives the complete booking payload from the `PaymentForm`.
    3.  It makes a `POST` request to your Flask `/api/verteil/order-create` endpoint.
    4.  Handles the response from Flask:
        *   If successful (PNR received):
            *   (Optional but recommended) Store booking summary in your portal's database.
            *   Trigger any necessary notifications (e.g., add to a queue for email).
            *   Return data to the client to redirect to `/confirmation` page with OrderID/PNR.
        *   If errors or warnings from Verteil (via Flask): Propagate these to the client.
*   **Key Concerns:**
    *   **Idempotency:** Consider how to prevent duplicate bookings if the user retries after a network glitch. Your Flask backend might need an idempotency key mechanism if Verteil doesn't provide one for `OrderCreate`.
    *   **Transactionality:** If storing in your DB, consider the overall transaction.
    *   **Security:** This action handles sensitive data before it goes to Flask.

**AI Assistant Task 2.8: Implement Booking Confirmation Page**

*   **Instructions:**
    1.  Create `app/(booking)/confirmation/page.tsx`.
    2.  Fetch/display booking details (PNR, ticket numbers, summary) based on an OrderID passed in query params.
    3.  Display any warnings from the booking process.
*   **Key Concerns:**
    *   Clear and reassuring confirmation message.

---

**Phase 3: Enhancements & Polish**

*   **User Accounts:** (Sign Up, Login, Profile, Booking History) - Requires authentication (e.g., NextAuth.js) and database.
*   **Admin Panel (Flask-Admin or custom):** For the travel agency to view/manage bookings.
*   **Advanced Search Filters & Sorting:** Implement on the results page.
*   **Ancillaries/Add-ons:** If Verteil NDC supports OrderChange/ServiceList for ancillaries.
*   **Seat Selection:** If Verteil NDC provides seat maps.
*   **Internationalization (i18n) & Localization (l10n).**
*   **Detailed Error Pages.**
*   **Performance Optimization:** Image optimization, code splitting, caching strategies (Next.js caching, Redis on backend).
*   **Logging & Monitoring:** Comprehensive logging on both Next.js (server-side) and Flask. Monitoring tools.
*   **Automated Testing:** Unit tests, integration tests for Flask API, E2E tests for frontend flows (e.g., using Playwright or Cypress).

---

**AI Assistant: General Technical Standards & Best Practices**

*   **Version Control:** Use Git meticulously. Feature branches, meaningful commit messages.
*   **Code Linting & Formatting:** Use ESLint, Prettier for consistent code style.
*   **TypeScript:** Leverage strong typing for robustness. Define clear interfaces/types for API payloads and complex objects (e.g., transformed offer data).
*   **Environment Variables:** Use `.env` files for all configurable parameters and secrets.
*   **API Design (Flask):** Follow RESTful principles where applicable.
*   **Frontend Component Design:** Atomic design principles or similar for structured components.
*   **Accessibility (a11y):** Ensure the frontend is accessible (WCAG AA).
*   **Documentation:**
    *   Code comments for complex logic.
    *   API documentation for your Flask backend (e.g., using Swagger/OpenAPI via a Flask extension).
    *   A brief developer guide for project setup and key architectural decisions.

---

This guide should provide a clear roadmap. The most challenging parts will be:
1.  The **data transformation layers** in `flight_service.py` to convert verbose Verteil RS into lean frontend-friendly JSON.
2.  **Managing state and context** (like `ShoppingResponseID`, `OfferID`, full ASRS/FPRS context) across the multi-step NDC flow, especially between Next.js and Flask.
3.  **Payment gateway integration** and correctly structuring the `PaymentCard` block for Verteil.

Start with the backend, get one flow working (e.g., AirShopping), then build the corresponding frontend, and iterate. Good luck, AI assistant! Let me know when you're ready to tackle specific code implementations for these tasks.