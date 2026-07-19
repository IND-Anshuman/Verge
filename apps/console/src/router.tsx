import { lazy, Suspense } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import AppShell from '@/components/templates/AppShell';

// Lazy load route pages
const FindingsView = lazy(() => import('@/pages/FindingsView'));
const FindingDetailView = lazy(() => import('@/pages/FindingDetailView'));
const AdminView = lazy(() => import('@/pages/AdminView'));
const AuditView = lazy(() => import('@/pages/AuditView'));
const ReplayView = lazy(() => import('@/pages/ReplayView'));
const FleetView = lazy(() => import('@/pages/FleetView'));
const ShiftHandoverView = lazy(() => import('@/pages/ShiftHandoverView'));
const KnowledgeView = lazy(() => import('@/pages/KnowledgeView'));
const GraphView = lazy(() => import('@/pages/GraphView'));
const MaintenanceView = lazy(() => import('@/pages/MaintenanceView'));

import { Skeleton, FindingCardSkeleton } from '@/components/atoms';

/* Route fallback — a skeleton shaped like the view being loaded, not a
   spinner island or anonymous card grid. */
function PageFallback() {
  const { pathname } = useLocation();

  // Board: filter bar + six state columns with card ghosts
  if (pathname === '/') {
    return (
      <div className="h-full w-full bg-bg p-4 flex flex-col gap-4 select-none" aria-busy="true" aria-label="Loading board">
        <div className="flex items-center justify-between border-b border-line pb-3">
          <div className="flex items-center gap-3">
            <Skeleton className="h-8 w-64" />
            <Skeleton className="h-8 w-72" />
          </div>
          <Skeleton className="h-4 w-28" />
        </div>
        <div className="flex gap-3 flex-1 min-h-0 overflow-hidden">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="flex-1 border border-line rounded-md bg-panel/30 flex flex-col gap-2 overflow-hidden">
              <div className="h-9 px-3 border-b border-line flex items-center justify-between">
                <Skeleton className="h-3 w-20" />
                <Skeleton className="h-4 w-5" />
              </div>
              <div className="p-2 flex flex-col gap-2">
                <FindingCardSkeleton />
                {i % 2 === 0 && <FindingCardSkeleton />}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Knowledge: corpus rail + ask column
  if (pathname.startsWith('/knowledge')) {
    return (
      <div className="h-full w-full bg-bg p-4 flex flex-col gap-4 select-none" aria-busy="true" aria-label="Loading knowledge">
        <div className="flex items-end justify-between border-b border-line pb-3">
          <div className="flex flex-col gap-2">
            <Skeleton className="h-5 w-44" />
            <Skeleton className="h-3 w-80" />
          </div>
          <Skeleton className="h-7 w-32" />
        </div>
        <div className="grid grid-cols-[300px_minmax(0,1fr)] gap-4 flex-1 min-h-0 overflow-hidden">
          <div className="border border-line rounded-md bg-panel p-3 flex flex-col gap-2">
            <Skeleton className="h-3 w-24" />
            <Skeleton className="h-14 w-full" />
            <Skeleton className="h-14 w-full" />
          </div>
          <div className="border border-line rounded-md bg-panel p-3 flex flex-col gap-3">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-32 w-full" />
          </div>
        </div>
      </div>
    );
  }

  // Default: document header + section blocks
  return (
    <div className="h-full w-full bg-bg p-4 flex flex-col gap-4 select-none" aria-busy="true" aria-label="Loading view">
      <div className="flex items-end justify-between border-b border-line pb-3">
        <div className="flex flex-col gap-2">
          <Skeleton className="h-5 w-48" />
          <Skeleton className="h-3 w-72" />
        </div>
        <Skeleton className="h-7 w-28" />
      </div>
      <div className="grid grid-cols-2 gap-4 flex-1 min-h-0 overflow-hidden">
        <div className="flex flex-col gap-3">
          <Skeleton className="h-3 w-32" />
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-20 w-full" />
        </div>
        <div className="flex flex-col gap-3">
          <Skeleton className="h-3 w-32" />
          <Skeleton className="h-44 w-full" />
        </div>
      </div>
    </div>
  );
}

import { RoleGuard } from '@/components/atoms/RoleGuard';

export default function AppRouter() {
  return (
    <Suspense fallback={<PageFallback />}>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<FindingsView />} />
          <Route path="/findings/:id" element={<FindingDetailView />} />
          <Route
            path="/admin"
            element={
              <RoleGuard allowedRoles={['Safety_Engineer', 'administrator']}>
                <AdminView />
              </RoleGuard>
            }
          />
          <Route
            path="/audit"
            element={
              <RoleGuard allowedRoles={['Safety_Engineer', 'administrator']}>
                <AuditView />
              </RoleGuard>
            }
          />
          <Route path="/replay" element={<ReplayView />} />
          <Route path="/fleet" element={<FleetView />} />
          <Route path="/knowledge" element={<KnowledgeView />} />
          <Route path="/graph" element={<GraphView />} />
          <Route path="/maintenance" element={<MaintenanceView />} />
          <Route
            path="/handover"
            element={
              <RoleGuard allowedRoles={['Safety_Engineer', 'administrator']}>
                <ShiftHandoverView />
              </RoleGuard>
            }
          />
          {/* Fallback redirect */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </Suspense>
  );
}
