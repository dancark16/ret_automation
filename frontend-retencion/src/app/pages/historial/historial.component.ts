import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatTableModule } from '@angular/material/table';
import { MatChipsModule } from '@angular/material/chips';
import { RetenciónService } from '../../services/retencion.service';
import { Retencion } from '../../models/retencion.model';

@Component({
    selector: 'app-historial',
    standalone: true,
    imports: [CommonModule, MatTableModule, MatChipsModule],
    templateUrl: './historial.component.html',
    styleUrl: './historial.component.scss'
})
export class HistorialComponent implements OnInit {
    retenciones: Retencion[] = [];
    cols = ['fecha', 'cliente', 'factura', 'retencion', 'total', 'estado', 'obs'];

    constructor(private svc: RetenciónService) { }

    ngOnInit() {
        this.svc.listar().subscribe(list => this.retenciones = list);
    }

    chipColor(s: string): string {
        const map: Record<string, string> = {
            completado: 'primary',
            error: 'warn',
            pendiente: 'accent',
            en_proceso: 'warn'
        };
        return map[s] ?? '';
    }

    total(r: Retencion): number {
        return r.renta_value + r.iva_value;
    }
}