import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  {
    path: 'dashboard',
    loadComponent: () => import('./pages/dashboard/dashboard.component').then(m => m.DashboardComponent)
  },
  {
    path: 'pendientes',
    loadComponent: () => import('./pages/pendientes/pendientes.component').then(m => m.PendientesComponent)
  },
  {
    path: 'detalle/:id',
    loadComponent: () => import('./pages/detalle/detalle.component').then(m => m.DetalleComponent)
  },
  {
    path: 'historial',
    loadComponent: () => import('./pages/historial/historial.component').then(m => m.HistorialComponent)
  },
];
