export interface Retencion {
    id: number;
    ret_number: string;
    ret_serial: string;
    client_name: string;
    invoice_sequential: string;
    invoice_date: string;
    renta_pct: number;
    renta_base: number;
    renta_value: number;
    iva_pct: number;
    iva_base: number;
    iva_value: number;
    status: 'pendiente' | 'en_proceso' | 'completado' | 'error';
    observation: string;
    created_at: string;
    processed_at: string | null;
}

export interface ProgressMsg {
    retencion_id: number;
    step: string;
    status: 'running' | 'ok' | 'error';
    detail: string;
}