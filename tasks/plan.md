# Implementation Plan: Camera Scanner Black Screen & Constraint Fix

## Overview
This plan addresses the black screen / frozen viewfinder state in `BarcodeScannerModal` caused by passing `{ facingMode: { ideal: facingMode } }` to `html5-qrcode` (which strictly requires `{ facingMode: facingMode }`), and adds full error visibility to the viewfinder so camera hardware/permission errors are never silently swallowed.

---

## Architecture Decisions

1. **Pass Valid `facingMode` String to `html5-qrcode`:**
   - `html5-qrcode`'s internal `createVideoConstraints` method explicitly throws `'facingMode' should be string or object with exact as key.` when receiving an object without `exact`.
   - In browser WebRTC standards, passing `{ facingMode: "environment" }` (without `exact`) is inherently treated as an ideal/soft constraint by the browser.
   - Update `scanner.start({ facingMode }, config, ...)` to supply the string directly.

2. **Propagate and Render Scanner Errors in Viewfinder:**
   - Expose `error` from `useBarcodeScanner` in `BarcodeScannerModal`.
   - Pass `error` to `ScannerViewfinder`.
   - Render an interactive error state with an explicit "Reintentar" button whenever `error` is present and scanning is inactive.

3. **Verify Against Real Validator Behavior:**
   - Update Vitest mocks and tests in `useBarcodeScanner.test.ts` to assert that `start` is called with `{ facingMode: "environment" }`.
   - Add test verifying error propagation to viewfinder.

---

## Task List Summary

### Phase 1: Fix Constraint Syntax in Scanner Hook
- Task 1: Replace invalid `{ ideal: facingMode }` constraint with `{ facingMode }` in `useBarcodeScanner.ts`
- Task 2: Update `useBarcodeScanner.test.ts` to assert valid facingMode string and test error state propagation
- **Checkpoint: Hook tests pass cleanly**

### Phase 2: Viewfinder Error State & Modal Integration
- Task 3: Add error display overlay with retry action in `ScannerViewfinder.tsx`
- Task 4: Connect scanner `error` prop from `useBarcodeScanner` in `BarcodeScannerModal.tsx`
- Task 5: Verify modal integration and error rendering in `BarcodeScannerModal.test.tsx`
- **Checkpoint: All component tests and full test suite pass**

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Single-camera devices (laptops) | Low | Standard `{ facingMode: "environment" }` automatically falls back to available front camera in browsers unless `exact` is specified. |
| User camera in use by another app | Medium | Surfaced error alert with "Reintentar" button gives user clear diagnostic and recovery path. |

---

## Open Questions
- *None.* Root cause is verified with exact library reproduction.
