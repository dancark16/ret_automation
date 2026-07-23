import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { Subscription } from 'rxjs';
import { RetenciónService } from '../../services/retencion.service';
import { WsService } from '../../services/ws.service';
import { Retencion, ProgressMsg } from '../../models/retencion.model';

interface Step {
    key: string;
    label: string;
    status: 'pending' | 'running' | 'ok' | 'error';
    detail: string;
}

@Component({
    selector: 'app-detalle',
    standalone: true,
    imports: [
        CommonModule,
        MatCardModule,
        MatButtonModule,
        MatIconModule,
        MatListModule,
        MatSnackBarModule,
        MatProgressSpinnerModule
    ],
    templateUrl: './detalle.component.html',
    styleUrl: './detalle.component.scss'
})
export class DetalleComponent implements OnInit, OnDestroy {
    r: Retencion | null = null;
    procesando = false;
    private sub?: Subscription;
    private id!: number;

    steps: Step[] = [
        { key: 'encolado', label: 'Encolado para Monica', status: 'pending', detail: '' },
        { key: 'monica_facturacion', label: 'Abriendo facturación', status: 'pending', detail: '' },
        { key: 'monica_factura', label: 'Buscando factura', status: 'pending', detail: '' },
        { key: 'monica_retenciones', label: 'Verificando retenciones', status: 'pending', detail: '' },
        { key: 'monica_obs', label: 'Guardando observaciones', status: 'pending', detail: '' },
        { key: 'pdf', label: 'Guardando PDF', status: 'pending', detail: '' },
        { key: 'excel', label: 'Registrando en Excel', status: 'pending', detail: '' },
    ];

    constructor(
        public router: Router,
        public svc: RetenciónService,
        private route: ActivatedRoute,
        private ws: WsService,
        private snack: MatSnackBar
    ) { }

    ngOnInit() {
        this.id = Number(this.route.snapshot.paramMap.get('id'));
        this.svc.detalle(this.id).subscribe(r => this.r = r);

        this.sub = this.ws.connect().subscribe((msg: ProgressMsg) => {
            if (msg.retencion_id !== this.id) return;
            const step = this.steps.find(s => s.key === msg.step);
            if (step) {
                step.status = msg.status as any;
                step.detail = msg.detail;
            }
            if (msg.step === 'finalizado') {
                this.procesando = false;
                this.svc.detalle(this.id).subscribe(r => this.r = r);
            }
        });
    }

    procesar() {
        if (!this.r) return;
        this.procesando = true;
        this.steps.forEach(s => { s.status = 'pending'; s.detail = ''; });
        this.svc.procesar(this.r.id).subscribe({
            error: (e) => {
                this.snack.open(e.error?.detail || 'Error', 'OK', { duration: 4000 });
                this.procesando = false;
            }
        });
    }

    get totalRet(): number {
        return (this.r?.renta_value ?? 0) + (this.r?.iva_value ?? 0);
    }

    icon(s: string): string {
        const map: Record<string, string> = {
            pending: 'radio_button_unchecked',
            running: 'hourglass_top',
            ok: 'check_circle',
            error: 'error'
        };
        return map[s] ?? '';
    }

    iconColor(s: string): string {
        const map: Record<string, string> = {
            pending: '#bbb',
            running: '#1565c0',
            ok: '#2e7d32',
            error: '#c62828'
        };
        return map[s] ?? '';
    }

    ngOnDestroy() { this.sub?.unsubscribe(); }
}