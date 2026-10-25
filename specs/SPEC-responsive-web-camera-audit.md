# Spec: Responsive Web Frontend & Device Camera Barcode Scanning

## Phase 0: Scope Check & Capability Map

Transforming `frontend-web` into a multi-device application operable across desktop displays and mobile phone browsers (iOS Safari, Android Chrome, mobile webviews), paired with hardware camera access for real-time item barcode scanning in the Audit section, clusters into distinct, independently testable capabilities:

| Module ID | Responsibility | Depends On |
|---|---|---|
| `responsive-shell` | Viewport handling (`100dvh`), responsive sidebar drawer navigation, mobile top bar, safe-area insets, and touch ergonomics | — |
| `camera-scanner` | Hardware camera stream lifecycle (`getUserMedia`), permission state machine (Prompt/Granted/Denied/Unavailable), `BarcodeDetector` / ZXing decoding engine, viewfinder overlay with targeting reticle, torch toggle, and track cleanup | — |
| `audit-mobile-flow` | Audit page mobile reflow, camera scan integration with search & auto-fill, tactile stepper buttons (≥ 48x48px), single-handed ergonomics, and instant audit mutation feedback | `responsive-shell`, `camera-scanner` |
| `responsive-views` | Mobile responsiveness for data-heavy sections (Catalog responsive table/card switcher, Dashboard KPI grid stacking, Reports horizontally scrollable tab bar, and Users list layout) | `responsive-shell` |

**Build Order:** `responsive-shell` → `camera-scanner` → `audit-mobile-flow` → `responsive-views`.

---

## 1. Objective

Provide warehouse personnel, supervisors, and store managers with a mobile-ready web frontend for the **Audit Global (SaaS Stock Deposit Control)** platform:
1. **Responsive Multi-Device Web UI**: Enable warehouse operators to use the web application seamlessly on desktop computers, tablets, and mobile phones (down to 360px viewport width) without horizontal overflow, tiny touch targets, or broken drawers.
2. **Camera-Based Barcode Scanning in Audit**: Allow warehouse operators on mobile phones or webcams to point their device camera at product barcodes (EAN-13, CODE-128, QR, UPC) to instantly identify articles in `AuditPage` without manual keyboard typing.
3. **Robust Hardware Permissions & Error States**: Handle browser camera permissions deterministically (initial prompt, user denial, hardware in-use errors, non-HTTPS insecure context), with clear user guidance and immediate manual fallback.
4. **Hardware Lifecycle Safety**: Guarantee zero camera/track leaks when navigating away, closing the scanner modal, or completing a scan, preventing battery drain and device locks.

---

## 2. Tech Stack

- **Framework:** Next.js 16.2 (App Router), React 19.2 (Server & Client Components)
- **Language:** TypeScript 5.x
- **Styling & Tokens:** Tailwind CSS v4, `shared/design-tokens/` (Glassmorphic palette, status colors, semantic elevation)
- **Icons:** `lucide-react` (Camera, ScanBarcode, Flashlight, FlipHorizontal, X, Check, Search)
- **Barcode Decoding Engine:** `html5-qrcode` (v2.3.8+) or Native `BarcodeDetector` API with ZXing polyfill fallback
- **Testing:** Vitest 2.1+, `@testing-library/react`, mock `navigator.mediaDevices`

---

## 3. Commands

- **Install Dependencies:**
  ```bash
  cd frontend-web && npm install html5-qrcode
  ```
- **Run Local Development Server (Desktop):**
  ```bash
  cd frontend-web && npm run dev
  ```
- **Run Local Development Server with Network Access (Mobile Testing via LAN/HTTPS):**
  ```bash
  cd frontend-web && npx next dev --hostname 0.0.0.0 --port 3000
  ```
  *(Note: Chrome/Safari require `localhost` or valid `https://` for `getUserMedia` camera access)*
- **Run Typecheck & Build:**
  ```bash
  cd frontend-web && npm run build
  ```
- **Run Linter:**
  ```bash
  cd frontend-web && npm run lint
  ```
- **Run Test Suite:**
  ```bash
  cd frontend-web && npm test
  ```

---

## 4. Project Structure

```
frontend-web/
├── app/
│   ├── globals.css                       # Viewport units, safe-area utilities, mobile touch adjustments
│   ├── layout.tsx                        # Meta viewport config (viewport-fit=cover)
│   ├── audit/
│   │   └── page.tsx                      # Audit page refactored with scanner trigger & mobile stepper
│   ├── catalog/
│   │   └── page.tsx                      # Responsive catalog container
│   ├── dashboard/
│   │   └── page.tsx                      # Responsive grid layout for metrics & quick access
│   ├── reports/
│   │   └── page.tsx                      # Touch-friendly horizontal tab navigation
│   └── users/
│       └── page.tsx                      # Responsive user cards / table
├── components/
│   ├── layout/
│   │   ├── DemoShell.tsx                 # Dynamic dvh viewport, mobile sidebar drawer management
│   │   ├── Sidebar.tsx                   # Slide-out drawer with backdrop on mobile, collapsed rail on desktop
│   │   └── TopBar.tsx                    # Compact mobile top bar, hamburger menu, quick avatar
│   ├── scanner/
│   │   ├── BarcodeScannerModal.tsx       # [NEW] Fullscreen / modal camera scanner overlay
│   │   ├── ScannerViewfinder.tsx         # [NEW] Camera video element, targeting reticle & scanning laser animation
│   │   └── ScannerPermissionState.tsx    # [NEW] Permission prompt, denied instructions, retry & manual fallback
│   └── ui/
│       └── DataTable.tsx                 # Dual-mode view: desktop table vs. mobile article cards
├── lib/
│   ├── hooks/
│   │   ├── useCameraPermissions.ts       # [NEW] Tracks permission state ('prompt' | 'granted' | 'denied' | 'unsupported')
│   │   └── useBarcodeScanner.ts          # [NEW] Hardware stream lifecycle, camera enumeration, torch control, track cleanup
│   └── utils/
│       └── haptics.ts                    # [NEW] Haptic vibration & audio chime triggers for successful scans
└── specs/
    └── SPEC-responsive-web-camera-audit.md # This specification document
```

---

## 5. Code Style & Technical Architecture

### 5.1 Dynamic Viewport & Safe-Area Ergonomics (`globals.css` & `DemoShell.tsx`)
Mobile browsers dynamically expand and retract the URL bar and navigation toolbar when scrolling. Fixed `100vh` causes unwanted layout shifts and cut-off submit buttons.
- Use `h-[100dvh]` (dynamic viewport height) and `min-h-[100dvh]`.
- Support mobile safe areas (`env(safe-area-inset-top)`, `env(safe-area-inset-bottom)`).

```tsx
// DemoShell.tsx Viewport Setup
<div className="flex h-[100dvh] w-full overflow-hidden bg-slate-50 text-slate-900 antialiased selection:bg-indigo-500 selection:text-white">
  {/* Collapsible Mobile Drawer & Desktop Sidebar */}
  <Sidebar mobileOpen={mobileSidebarOpen} onMobileClose={() => setMobileSidebarOpen(false)} />
  <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative bg-slate-50">
    <TopBar onMenuToggle={() => setMobileSidebarOpen(prev => !prev)} />
    <main className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8 space-y-6 pb-[calc(1rem+env(safe-area-inset-bottom))]">
      {children}
    </main>
  </div>
</div>
```

### 5.2 Camera Stream & Hardware Lifecycle Management (`useBarcodeScanner.ts`)
To prevent device locking and battery drain:
- Always obtain `stream = await navigator.mediaDevices.getUserMedia(...)`.
- When stopping, unmounting, or succeeding, **iterate through all tracks and explicitly call `.stop()`**.
- Handle secure context verification (`window.isSecureContext`).

```typescript
// Sample Scanner Hook Lifecycle Contract
export type CameraPermissionStatus = "idle" | "requesting" | "granted" | "denied" | "unsupported";

export function useBarcodeScanner({
  onDetected,
  active,
}: {
  onDetected: (barcode: string) => void;
  active: boolean;
}) {
  const [status, setStatus] = useState<CameraPermissionStatus>("idle");
  const [torchOn, setTorchOn] = useState(false);
  const [hasTorch, setHasTorch] = useState(false);
  const streamRef = useRef<MediaStream | null>(null);

  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setTorchOn(false);
  }, []);

  // Guarantee track cleanup on unmount or active=false
  useEffect(() => {
    if (!active) {
      stopCamera();
    }
    return () => {
      stopCamera();
    };
  }, [active, stopCamera]);

  return { status, startScanning, stopCamera, torchOn, toggleTorch, hasTorch };
}
```

### 5.3 React 19 State-in-Effect Compliance
Never call `setState` synchronously within `useEffect` bodies during render cycles (flagged by React 19 `react-hooks/set-state-in-effect`).
- Derive action types during render calculation rather than through an effect.
- State transitions must occur inside asynchronous handlers or event callbacks.

```typescript
// Derived state calculation pattern (No effect needed)
const derivedActionType = useMemo(() => {
  if (!selectedArticle || physicalCount === "") return null;
  const count = Number(physicalCount);
  if (count === selectedArticle.stock_real) return "none";
  return count > selectedArticle.stock_real ? "surplus" : "shortage";
}, [physicalCount, selectedArticle]);
```

### 5.4 Touch-Friendly Minimum Tap Targets (WCAG AA)
All interactive controls on mobile (stepper increment/decrement buttons, camera toggle button, search input, chips, action buttons) must have an active target size of at least **48x48px** with appropriate touch feedback (`active:scale-95`).

---

## 6. Detailed Capabilities & User Flows

### Capability 1: Responsive Navigation & Shell (`responsive-shell`)
1. **Desktop View (≥ 1024px):**
   - Full left sidebar with expandable/collapsible toggle (`w-64` / `w-20`).
   - Top bar displays breadcrumb, user name, role badge, and logout.
2. **Mobile View (< 768px):**
   - Sidebar transforms into a touch-enabled slide-out drawer (`fixed inset-y-0 left-0 z-50 w-72`).
   - Semi-transparent backdrop (`bg-black/60 backdrop-blur-sm`) closes drawer on tap.
   - Any navigation click automatically closes the drawer.
   - Top bar displays Hamburger icon button (`Menu`), truncated view title, user avatar circle, and logout button.

### Capability 2: Camera Barcode Scanner Component (`camera-scanner`)
1. **Activation:**
   - In `AuditPage`, an prominent "Scan Barcode" camera icon button (`<button type="button" aria-label="Escanear con cámara">`) sits inside the search bar.
   - Clicking opens the `BarcodeScannerModal`.
2. **Permission Lifecycle:**
   - **Step 1 (Check Context):** If `!window.isSecureContext` and hostname is not `localhost`, display: *"El acceso a la cámara requiere conexión segura HTTPS"*.
   - **Step 2 (Prompt):** Display non-blocking prompt explaining why camera permission is needed before invoking `getUserMedia`.
   - **Step 3 (Granted):** Render live video feed in `ScannerViewfinder` with targeting reticle, scanning line animation, camera flip (back/front), and flashlight toggle (if supported by track capabilities).
   - **Step 4 (Denied):** Display friendly alert explaining that camera access was blocked, with step-by-step instructions on enabling permissions in Chrome/Safari site settings, plus a button to return to manual typing.
3. **Scan Execution:**
   - The scanner continuously parses frames using `BarcodeDetector` (formats: `ean_13`, `code_128`, `qr_code`, `upc_a`, `upc_e`, `code_39`) or `html5-qrcode`.
   - Upon valid detection:
     - Trigger haptic vibration (`navigator.vibrate([80])`).
     - Emit scan chime audio.
     - Call `onDetected(code)`.
     - Immediately stop all camera tracks and close modal.

### Capability 3: Mobile Audit Workflow (`audit-mobile-flow`)
1. **Fast-path Scan to Item:**
   - Decoded barcode triggers `client.getArticuloByBarcode(code)`.
   - If exact match found: automatically selects article, loads current stock, and focuses the counted stepper.
   - If not found by exact barcode: queries `client.searchArticulos(code)` or displays clear error badge: *"Código [X] no encontrado en catálogo"*.
2. **Mobile Stepper & Discrepancy Form:**
   - Stack item metadata (Marca, Familia, Código) cleanly on small screens without column collision.
   - Stepper provides large, comfortable buttons:
     - Minus button (disabled at 0): `h-12 w-12`
     - Physical count numeric input: centered font-extrabold text
     - Plus button: `h-12 w-12`
   - Quick adjustment chips (`+1`, `+5`, `+10`) for rapid counting.
   - Full-width "Registrar Auditoría" primary action button fixed or clearly visible with `pb-safe`.

### Capability 4: Responsive Catalog, Dashboard & Reports (`responsive-views`)
1. **Catalog Page (`app/catalog/page.tsx` & `DataTable.tsx`):**
   - On screens `< 768px`, replace wide multi-column table with responsive Article Cards (`block md:hidden`), displaying:
     - Description & Barcode
     - Brand & Family tags
     - Stock number & Audit status badge
   - Filter inputs stack vertically (`flex-col sm:flex-row`).
2. **Dashboard Page (`app/dashboard/page.tsx`):**
   - KPI cards reflow from `grid-cols-3` to `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3`.
   - Quick Action cards expand to full width with touch indicators.
3. **Reports Page (`app/reports/page.tsx`):**
   - Tab bar becomes horizontally scrollable with touch momentum (`overflow-x-auto no-scrollbar`).
   - Date range pickers stack vertically on phones.

---

## 7. Testing Strategy

1. **Unit & Hook Tests (`vitest`):**
   - `useCameraPermissions.test.ts`: Verify state transitions for `granted`, `denied`, and `unsupported` navigator objects.
   - `useBarcodeScanner.test.ts`: Mock `navigator.mediaDevices.getUserMedia` and verify that calling `stopCamera()` or unmounting stops all media stream tracks.
2. **Component Integration Tests:**
   - `BarcodeScannerModal.test.tsx`:
     - Test that permission prompt appears.
     - Test that denied state displays instructions and dismiss button.
     - Test that successful scan invokes callback with trimmed barcode string.
   - `AuditPage.test.tsx`:
     - Test simulated scan event sets `barcodeQuery` and loads article.
     - Verify touch-stepper increments and decrements count accurately.
3. **Responsive Viewport Verification:**
   - Test layouts at:
     - Mobile: `360x640` (Android compact), `390x844` (iPhone 12/13/14/15)
     - Tablet: `768x1024` (iPad portrait)
     - Desktop: `1280x800` & `1920x1080`
   - Zero horizontal page scrollbars on viewports `360px - 768px`.

---

## 8. Boundaries

- **Always do:**
  - Verify `window.isSecureContext` before accessing camera devices.
  - Release camera hardware tracks (`track.stop()`) on modal close, navigation, and unmount.
  - Adhere to `shared/design-tokens/` for colors, radiuses, and glassmorphic styling.
  - Support manual barcode entry as a first-class alternative for users without camera permissions or devices lacking cameras.
  - Enforce touch target minimum size of 48x48px on mobile controls.
- **Ask first:**
  - Introducing heavy native mobile scanning bundles (> 150KB gzip).
  - Modifying backend endpoints or database schemas (frontend scope only).
- **Never do:**
  - Leave video tracks open in the background after scanning or leaving the audit route.
  - Trap mobile users in an unclosable camera modal on permission denial.
  - Break desktop layout or remove existing desktop capabilities while adding mobile responsiveness.
  - Bypass `DataClientPort` by calling raw backend URLs directly.

---

## 9. Success Criteria

1. **Camera Barcode Recognition:**
   - Pointing device camera at common barcodes (EAN-13, CODE-128, QR) decodes successfully within 500ms under standard warehouse lighting.
   - Scanning instantly selects the matching article in `AuditPage` without manual keystrokes.
2. **Permission Handling:**
   - Clean permission request on user action (never unsolicited on initial page load).
   - Graceful denial screen with clear instructions and 1-tap manual fallback.
   - Zero camera lockups or active hardware indicators after modal dismissal.
3. **Mobile Browser Responsiveness:**
   - Tested and verified on mobile screen widths (360px, 375px, 390px, 414px) and desktop (> 1024px).
   - No horizontal body scrolling (`overflow-x: hidden`).
   - Dynamic mobile viewport height (`100dvh`) avoids address-bar jumpiness.
   - Slide-out navigation drawer works smoothly with backdrop tap-to-dismiss.
4. **Code Quality & Build:**
   - `npm run lint` passes with 0 errors.
   - `npm run build` generates Next.js production build without hydration or type errors.
   - `npm test` passes all unit and integration test suites.

---

## 10. Open Questions for Human Review

1. **Barcode Library Selection:**
   - Option A: `html5-qrcode` (battle-tested, handles canvas rendering, automatic fallback to ZXing on Safari/Firefox, ~45KB).
   - Option B: Lightweight native `BarcodeDetector` with custom video element + dynamic ZXing fallback only when `window.BarcodeDetector` is undefined.
   *(Recommendation: `html5-qrcode` for maximum out-of-the-box cross-browser stability across iOS Safari and Android Chrome).*
**ANSWER**: Implement the Option A. 

2. **Scanner Placement & UX in Audit:**
   - Option A (Modal Viewfinder): Clicking the camera icon opens an overlay modal with targeting frame and flash toggle. Once scanned, modal auto-closes and populates the item.
   - Option B (Inline Collapsible Viewfinder): The camera view expands right above the search bar inline in the page.
   *(Recommendation: Option A - Modal Viewfinder provides the cleanest experience on small phone screens without pushing form content off screen).*
**ANSWER**: Implement the Option A. 

3. **Scan Feedback:**
   - Should successful scans trigger an optional short audio beep alongside haptic vibration?
**ANSWER**: It is not necessary the short audio, but we can add a haptic vibration. 