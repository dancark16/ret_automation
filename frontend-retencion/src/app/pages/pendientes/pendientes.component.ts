import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { RetenciónService } from '../../services/retencion.service';
import { Retencion } from '../../models/retencion.model';

@Component({
    selector: 'app-pendientes',
    standalone: true,
    imports: [CommonModule, MatTableModule, MatButtonModule, MatChipsModule, MatIconModule],
    templateUrl: './pendientes.component.html',
    styleUrl: './pendientes.component.scss'
})
export class PendientesComponent implements OnInit {
    retenciones: Retencion[] = [];
    cols = ['fecha', 'cliente', 'factura', 'retencion', 'estado', 'accion'];

    constructor(public router: Router, private svc: RetenciónService) { }

    ngOnInit() {
        this.svc.listar().subscribe(list =>
            this.retenciones = list.filter(r => r.status !== 'completado')
        );
    }

    chipColor(status: string): string {
        const map: Record<string, string> = {
            pendiente: 'accent',
            en_proceso: 'warn',
            error: 'warn',
            completado: 'primary'
        };
        return map[status] ?? '';
    }

    eliminar(id: number, event: Event) {
        event.stopPropagation();
        if (!confirm('¿Eliminar esta retención?')) return;
        this.svc.eliminar(id).subscribe(() =>
            this.retenciones = this.retenciones.filter(r => r.id !== id)
        );
    }
}