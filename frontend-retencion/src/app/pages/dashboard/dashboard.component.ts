import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { RetenciónService } from '../../services/retencion.service';

@Component({
    selector: 'app-dashboard',
    standalone: true,
    imports: [CommonModule, MatCardModule, MatButtonModule, MatIconModule, MatSnackBarModule],
    templateUrl: './dashboard.component.html',
    styleUrl: './dashboard.component.scss'
})
export class DashboardComponent implements OnInit {
    pendientes = 0;
    completadas = 0;
    errores = 0;
    syncing = false;

    constructor(
        public router: Router,
        private svc: RetenciónService,
        private snack: MatSnackBar
    ) { }

    ngOnInit() { this.cargar(); }

    cargar() {
        this.svc.listar().subscribe(list => {
            this.pendientes = list.filter(r => r.status === 'pendiente').length;
            this.completadas = list.filter(r => r.status === 'completado').length;
            this.errores = list.filter(r => r.status === 'error').length;
        });
    }

    sincronizar() {
        this.syncing = true;
        this.svc.sincronizarSRI().subscribe({
            next: (r) => {
                this.snack.open(r.mensaje, 'OK', { duration: 4000 });
                this.syncing = false;
                setTimeout(() => this.cargar(), 3000);
            },
            error: () => {
                this.snack.open('Error al conectar con el SRI', 'OK', { duration: 4000 });
                this.syncing = false;
            }
        });
    }

    onFile(files: FileList | null) {
        if (!files?.length) return;
        this.svc.uploadPdf(files[0]).subscribe({
            next: (r) => {
                this.snack.open(`PDF cargado: ${r.ret_number}`, 'OK', { duration: 3000 });
                this.cargar();
            },
            error: (e) => this.snack.open(e.error?.detail || 'Error al subir PDF', 'OK', { duration: 4000 })
        });
    }
}