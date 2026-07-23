import { Injectable, NgZone } from '@angular/core';
import { Observable, Subject } from 'rxjs';
import { environment } from '../../environments/environment';
import { ProgressMsg } from '../models/retencion.model';

@Injectable({ providedIn: 'root' })
export class WsService {
    private ws: WebSocket | null = null;
    private subject = new Subject<ProgressMsg>();

    constructor(private zone: NgZone) { }

    connect(): Observable<ProgressMsg> {
        if (!this.ws || this.ws.readyState > 1) {
            this.ws = new WebSocket(environment.wsUrl);
            this.ws.onmessage = (e) => {
                this.zone.run(() => this.subject.next(JSON.parse(e.data)));
            };
            this.ws.onclose = () => setTimeout(() => this.connect(), 3000);
        }
        return this.subject.asObservable();
    }

    ping() {
        if (this.ws?.readyState === 1) this.ws.send('ping');
    }
}