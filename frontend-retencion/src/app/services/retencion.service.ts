import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment';
import { Retencion } from '../models/retencion.model';

@Injectable({ providedIn: 'root' })
export class RetenciónService {
    private base = environment.apiUrl;

    constructor(private http: HttpClient) { }

    listar() {
        return this.http.get<Retencion[]>(`${this.base}/api/retenciones`);
    }

    detalle(id: number) {
        return this.http.get<Retencion>(`${this.base}/api/retenciones/${id}`);
    }

    uploadPdf(file: File) {
        const fd = new FormData();
        fd.append('file', file);
        return this.http.post<Retencion>(`${this.base}/api/retenciones/upload`, fd);
    }

    procesar(id: number) {
        return this.http.post<Retencion>(`${this.base}/api/retenciones/${id}/procesar`, {});
    }

    sincronizarSRI() {
        return this.http.post<{ ok: boolean; mensaje: string }>(`${this.base}/api/sri/sincronizar`, {});
    }

    pdfUrl(id: number) {
        return `${this.base}/api/retenciones/${id}/pdf`;
    }

    eliminar(id: number) {
        return this.http.delete(`${this.base}/api/retenciones/${id}`);
    }
}