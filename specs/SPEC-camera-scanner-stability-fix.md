# Spec: Camera Barcode Scanner Stability & Multi-Platform Crash Fix

## Status
- **Lifecycle:** Approved for Implementation
- **Capability:** `camera-scanner` resilience & cross-platform stability
- **Target Platforms:** Android Chrome (Samsung Galaxy S21 / One UI), Linux Chromium / Brave (Snap & Native), iOS Safari, Desktop Webcams

---

## 1. Objective

Resolve the hardware camera initialization freeze and subsequent browser crash (**Error code: `SIGILL` / "Aw, Snap!"**) occurring when launching the barcode scanner in `AuditPage` (`/audit`) on both desktop Linux browsers (Brave / Chromium) and mobile devices (Samsung Galaxy S21 running Android Chrome).

### Core Goals:
1. **Eliminate Browser Crashes (`SIGILL` / Mojo GPU IPC Failures):** Prevent Chromium's GPU channel from crashing due to null frame texture transfers during camera spin-up.
2. **Prevent Hardware Sensor Locks on Android / Samsung:** Eliminate rapid `getUserMedia` churn (double-invocation probe) that collides with Samsung One UI Camera2 HAL hardware locks.
3. **Resilient Camera Resolution & Device Fallback:** Support single-webcam desktop/laptop environments and multi-lens mobile devices seamlessly using flexible constraints (`ideal: "environment"`).
4. **Zero Track Leaks & Strict Race Condition Handling:** Guarantee that quick opening, closing, or navigating away during camera startup never leaves orphaned media tracks or unhandled promise rejections.
5. **Native C++ Barcode Detection Engine:** Activate Chromium's native `BarcodeDetector` API to drop CPU usage by >80% and eliminate heavy canvas drawing loops on mobile devices.

---

## 2. Root Cause Analysis

### 2.1 The Crash (`SIGILL`)
- **System Traps:** In Chromium (Brave / Chrome), `IMMEDIATE_CRASH()` is invoked when an IPC validation check fails on `gpu.mojom.GpuChannel` with `VALIDATION_ERROR_UNEXPECTED_NULL_POINTER`.
- On x86_64, `IMMEDIATE_CRASH()` executes the `ud2` instruction (Illegal Opcode); on ARM64, it executes `brk` / undefined instruction.
- The OS delivers signal 4 (`SIGILL`), killing the renderer tab.
- **Trigger:** `Html5Qrcode` initializes video frame extraction to a 2D canvas via `drawImage()` before the `<video>` element has reached a non-zero, playing state with valid hardware backing buffers.

### 2.2 The Camera Sensor Lock (Samsung Galaxy S21)
- `useCameraPermissions.requestPermission()` called `getUserMedia()` and immediately invoked `track.stop()`.
- Milliseconds later, `useBarcodeScanner.ts` invoked `Html5Qrcode.start()`, requesting `getUserMedia()` again.
- In Samsung One UI (Android Camera2 HAL), releasing a camera sensor lock is asynchronous and takes between 300ms and 1000ms. Immediate re-acquisition causes the camera service to reject or stall the stream, leaving the UI permanently frozen on *"Iniciando cámara..."* until the GPU watchdog kills the tab.

### 2.3 Strict Constraints Failure
- Requesting exact `{ facingMode: "environment" }` causes constraint failures or invalid device selections on laptops/desktops equipped only with front-facing webcams.

---

## 3. Tech Stack & Key Dependencies

- **Framework:** Next.js 16.2.10 (App Router), React 19.2.4
- **Language:** TypeScript 5.x
- **Barcode Engine:** `html5-qrcode` (v2.3.8) with `experimentalFeatures.useBarCodeDetectorIfSupported: true`
- **Testing:** Vitest 2.1.8, `@testing-library/react`, `@testing-library/dom`
- **Target Browsers:** Chromium 120+, Mobile Chrome 120+, Safari 16+, Firefox 120+

---

## 4. Commands

```bash
# Workspace
cd frontend-web

# Run test suite
npm test

# Run focused scanner tests
npx vitest run components/scanner/BarcodeScannerModal.test.tsx lib/hooks/useCameraPermissions.test.ts lib/hooks/useBarcodeScanner.test.ts

# Typecheck & Build
npm run build

# Run linter
npm run lint

# Start development server
npm run dev
```

---

## 5. Project Structure

```
frontend-web/
├── components/scanner/
│   ├── BarcodeScannerModal.tsx          # Scanner modal container & lifecycle orchestrator
│   ├── BarcodeScannerModal.test.tsx     # Integration unit tests for modal dialog
│   ├── ScannerViewfinder.tsx            # Viewfinder UI, reticle, laser animation & timeout fallback
│   └── ScannerPermissionState.tsx       # Idle prompt & denied permission recovery UI
├── lib/hooks/
│   ├── useCameraPermissions.ts          # Non-destructive permission query & state machine
│   ├── useCameraPermissions.test.ts     # Permission state transitions unit tests
│   ├── useBarcodeScanner.ts             # Race-free camera lifecycle, native detector, torch
│   └── useBarcodeScanner.test.ts        # Scanner lifecycle & detection unit tests
```

---

## 6. Architecture & Code Specifications

### 6.1 `useCameraPermissions.ts` (Non-Destructive Querying)
1. **Silent Permission Query:** Check `navigator.permissions.query({ name: "camera" as PermissionName })` on mount if supported. If already `"granted"`, transition directly to `"granted"` without requesting hardware.
2. **Eliminate Probe Track Churn:** When `requestPermission()` is triggered by user click:
   - If `navigator.permissions` is available and already granted, return `true` immediately.
   - If hardware acquisition is required, acquire stream with flexible constraints `{ video: { facingMode: { ideal: "environment" } } }`.
   - **Crucial:** Add a release safety delay (`150ms`) before resolving `requestPermission()`, giving the OS/HAL driver sufficient time to transition cleanly before `Html5Qrcode` attaches.

### 6.2 `useBarcodeScanner.ts` (Crash-Resilient Scanner Lifecycle)
1. **Enable Native BarcodeDetector:**
   ```ts
   const scanner = new Html5Qrcode(elementId, {
     formatsToSupport: [
       Html5QrcodeSupportedFormats.EAN_13,
       Html5QrcodeSupportedFormats.CODE_128,
       Html5QrcodeSupportedFormats.QR_CODE,
       Html5QrcodeSupportedFormats.UPC_A,
     ],
     verbose: false,
     experimentalFeatures: {
       useBarCodeDetectorIfSupported: true,
     },
   });
   ```
2. **Flexible Camera Constraints:**
   ```ts
   const cameraConfig = {
     facingMode: { ideal: facingMode },
   };
   ```
3. **Throttled Mobile FPS:** Reduce FPS from `15` to `10` to avoid thermal throttling and main thread lockup.
4. **Race Condition Lock (`startPromiseRef` & State Machine):**
   - Track active initialization: `isStartingRef = useRef(false)`.
   - Track initialization promise: `startPromiseRef = useRef<Promise<void> | null>(null)`.
   - In `stopScanning()`: If `isStartingRef.current` is true, wait for `startPromiseRef.current` to resolve/reject before executing `scanner.stop()` and `scanner.clear()`.
   - Prevent simultaneous double `scanner.start()` calls.
5. **Video Surface Dimension Guard:**
   - In `qrbox`: Verify that `viewfinderWidth > 0` and `viewfinderHeight > 0`. Fallback to minimum safe box `{ width: 200, height: 150 }` if zero to prevent division by zero or NaN dimensions in canvas drawing.
6. **Torch & Capability Discovery:**
   - Use `scanner.getRunningTrackCameraCapabilities()` or track inspection safely without assuming undocumented methods exist.

### 6.3 `ScannerViewfinder.tsx` (Timeout Warning State)
- If `isInitializing` persists for longer than 7 seconds, display a helpful message:
  *"La cámara está tardando en responder. Asegúrese de que ninguna otra aplicación esté usando la cámara."*
  with a **"Reintentar"** button that restarts the scan sequence.

---

## 7. Testing Strategy

### Unit & Integration Tests (Vitest):
1. **`useCameraPermissions.test.ts`:**
   - Test `permissions.query` fast path when permission is already `"granted"`.
   - Test non-secure context fallback (`isSecureContext === false`).
   - Test error mapping (`NotAllowedError` -> `denied`, `NotFoundError` -> `unsupported`).
   - Test graceful cooldown release.
2. **`useBarcodeScanner.test.ts`:**
   - Test initialization with `useBarCodeDetectorIfSupported: true`.
   - Test graceful shutdown when `stopScanning()` is invoked while initialization is in progress.
   - Test camera flip toggle (`facingMode` transitions).
   - Test barcode detection callback execution and haptic feedback.
3. **`BarcodeScannerModal.test.tsx`:**
   - Test seamless transition from permission grant to viewfinder render.
   - Test clean unmount without unhandled promise rejections.

---

## 8. Boundaries

- **Always:**
  - Preserve responsive UI layouts and Glassmorphism styling tokens.
  - Keep camera streams scoped to active scanning sessions (zero background leaks).
  - Use `ideal: "environment"` to support both desktop webcams and mobile rear cameras.
  - Test all changes using `npm test` and `npm run build` in `frontend-web`.
- **Ask First:**
  - Adding new third-party scanning libraries (e.g. replacing `html5-qrcode` with `@zxing/browser` or `@ericblade/quagga2`).
  - Changing public callback props of `BarcodeScannerModalProps`.
- **Never:**
  - Hardcode strict `facingMode: { exact: "environment" }`.
  - Reintroduce rapid throwaway `getUserMedia()` calls without hardware lock release buffering.
  - Suppress Chromium crash diagnostics or ignore track cleanup errors silently.

---

## 9. Success Criteria

- [ ] **No `SIGILL` crashes:** Barcode scanner opens cleanly on Linux Brave/Chrome with hardware acceleration enabled.
- [ ] **No Android camera freeze:** Barcode scanner opens and renders video feed within 1.5s on Samsung Galaxy S21 in Chrome.
- [ ] **Single Webcam Desktop Support:** Barcode scanner functions properly on laptops/desktops with only a front-facing camera.
- [ ] **Clean Lifecycle:** Closing the modal immediately stops hardware camera indicator LED/dot on all devices.
- [ ] **Full Test Suite Passing:** All 17+ test files in `frontend-web` pass without warnings or regressions.
