# Tasks: Camera Barcode Scanner Black Screen & Constraint Fix

## Phase 1: Fix Constraint Syntax in Scanner Hook

### Task 1: Replace invalid `{ ideal: facingMode }` constraint with `{ facingMode }` in `useBarcodeScanner.ts`
- **Description:** In `frontend-web/lib/hooks/useBarcodeScanner.ts`, change line 176 from `await scanner.start({ facingMode: { ideal: facingMode } }, ...)` to `await scanner.start({ facingMode }, ...)`. This complies with `html5-qrcode`'s constraint parser and allows the scanner to initialize without throwing an exception.
- **Acceptance criteria:**
  - [x] `scanner.start` receives `{ facingMode }` where `facingMode` is a string (`"environment"` or `"user"`).
  - [x] No exception is thrown by `html5-qrcode` during initialization.
  - [x] `isScanning` transitions to `true` when scanner starts successfully.
- **Verification:**
  - [x] `cd frontend-web && npx vitest run lib/hooks/useBarcodeScanner.test.ts`
- **Dependencies:** None
- **Files touched:**
  - `frontend-web/lib/hooks/useBarcodeScanner.ts`
- **Estimated scope:** XS (1 file, 1 line)

---

### Task 2: Update `useBarcodeScanner.test.ts` to assert valid facingMode string and test error state propagation
- **Description:** Update tests in `frontend-web/lib/hooks/useBarcodeScanner.test.ts` to assert `mockStart` is called with `{ facingMode: "environment" }`. Add a test verifying that when `mockStart` rejects with an error, `error` state is populated and `isScanning` is set to `false`.
- **Acceptance criteria:**
  - [x] Test verifies `mockStart` is called with `{ facingMode: "environment" }`.
  - [x] Test verifies that failure in `mockStart` populates `result.current.error`.
- **Verification:**
  - [x] `cd frontend-web && npx vitest run lib/hooks/useBarcodeScanner.test.ts`
- **Dependencies:** Task 1
- **Files touched:**
  - `frontend-web/lib/hooks/useBarcodeScanner.test.ts`
- **Estimated scope:** S (1 file)

---

## Checkpoint 1: Hook Constraint and Error Handling
- [x] All tests in `useBarcodeScanner.test.ts` pass.
- [x] No regressions in `useCameraPermissions.test.ts`.

---

## Phase 2: Viewfinder Error State & Modal Integration

### Task 3: Add error display overlay with retry action in `ScannerViewfinder.tsx`
- **Description:** Update `frontend-web/components/scanner/ScannerViewfinder.tsx` to accept an optional `error?: string | null` prop. When `error` is present and `!isInitializing && !isScanning`, render a styled error card with an alert icon, the error message, and a "Reintentar" button that invokes `onRetry`.
- **Acceptance criteria:**
  - [x] `ScannerViewfinderProps` includes `error?: string | null`.
  - [x] When `error` is truthy and not initializing/scanning, an accessible alert (`role="alert"`) overlay is displayed.
  - [x] Clicking "Reintentar" executes `onRetry`.
- **Verification:**
  - [x] `cd frontend-web && npx vitest run components/scanner/BarcodeScannerModal.test.tsx`
- **Dependencies:** Task 1
- **Files touched:**
  - `frontend-web/components/scanner/ScannerViewfinder.tsx`
- **Estimated scope:** S (1 file)

---

### Task 4: Connect scanner `error` prop from `useBarcodeScanner` in `BarcodeScannerModal.tsx`
- **Description:** In `frontend-web/components/scanner/BarcodeScannerModal.tsx`, destructure `error: scannerError` from `useBarcodeScanner` and pass `error={scannerError}` to `ScannerViewfinder`.
- **Acceptance criteria:**
  - [x] `scannerError` is passed as `error` prop to `ScannerViewfinder`.
  - [x] Viewfinder receives runtime errors if camera startup fails.
- **Verification:**
  - [x] `cd frontend-web && npx vitest run components/scanner/BarcodeScannerModal.test.tsx`
- **Dependencies:** Task 3
- **Files touched:**
  - `frontend-web/components/scanner/BarcodeScannerModal.tsx`
- **Estimated scope:** XS (1 file)

---

### Task 5: Verify modal integration and error rendering in `BarcodeScannerModal.test.tsx`
- **Description:** Update `frontend-web/components/scanner/BarcodeScannerModal.test.tsx` to add a test case where `useBarcodeScanner` returns an error, ensuring the error message is displayed to the user inside the viewfinder.
- **Acceptance criteria:**
  - [x] All existing 5 tests in `BarcodeScannerModal.test.tsx` pass.
  - [x] New test verifies that scanner error renders error alert with retry button.
  - [x] Full Vitest suite (`npm test`) passes with zero failures.
  - [x] Production build (`npm run build`) and lint (`npm run lint`) pass.
- **Verification:**
  - [x] `cd frontend-web && npm test`
  - [x] `cd frontend-web && npm run build`
- **Dependencies:** Task 4
- **Files touched:**
  - `frontend-web/components/scanner/BarcodeScannerModal.test.tsx`
- **Estimated scope:** S (1 file)

---

## Final Checkpoint
- [x] 17 test files and all 118 tests passing in `frontend-web`.
- [x] Build (`npm run build`) completes with zero type errors.
- [x] Camera opens with video feed, and any hardware/driver errors are surfaced visually with retry capability.
