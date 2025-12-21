# Ejemplos de Payloads para Semantic Adapter
Endpoint: `POST /api/v1/ingest`

## 1. Propiedad Inmobiliaria (Venta)
```json
{
  "content_id": "prop-001",
  "source": "crm_inmobiliario",
  "title": "Apartamento de Lujo en Escazú",
  "body_content": "Espectacular apartamento en venta en Torre Laureles, Escazú. Cuenta con 3 habitaciones, 2.5 baños, cuarto de servicio y parqueo para 2 vehículos. Amenidades incluyen piscina, gimnasio y seguridad 24/7. Precio de venta: $350,000. Área habitable de 180m2. Acabados de lujo con sobres de granito y pisos de porcelanato.",
  "metadata": {
    "client_id": "inmo-premium",
    "category": "propiedad_venta",
    "url": "https://inmo-premium.com/propiedades/escazu-laureles-001",
    "source_timestamp": "2023-10-25T10:00:00Z",
    "precio": 350000,
    "ubicacion": "Escazú, San José",
    "habitaciones": 3
  },
  "hash": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
}
```

## 2. Vehículo (Venta)
```json
{
  "content_id": "auto-055",
  "source": "web_dealer",
  "title": "Toyota Fortuner 2023 2.8L Diesel",
  "body_content": "Toyota Fortuner año 2023, motor 2.8 litros turbo diesel intercooler. Transmisión automática de 6 velocidades, tracción 4x4. Asientos de cuero, capacidad para 7 pasajeros. Kilometraje: 15,000 km. Color Blanco Perlado. Incluye paquete de seguridad Toyota Safety Sense. Garantía de fábrica vigente.",
  "metadata": {
    "client_id": "toyota-dealer-cr",
    "category": "vehiculos",
    "url": "https://toyotacr.com/usados/fortuner-2023",
    "source_timestamp": "2023-11-10T14:30:00Z",
    "modelo": "Fortuner",
    "marca": "Toyota",
    "anio": 2023,
    "combustible": "Diesel"
  },
  "hash": "z9y8x7w6v5u4t3s2r1q0p9o8n7m6l5k4"
}
```

## 3. Preguntas Frecuentes (FAQ) - Servicio al Cliente
```json
{
  "content_id": "faq-shipping-02",
  "source": "zendesk_kb",
  "title": "Políticas de Envío y Devoluciones",
  "body_content": "¿Cuánto tiempo tarda el envío? Los envíos dentro del Gran Área Metropolitana (GAM) tardan de 24 a 48 horas hábiles. Para zonas rurales, el tiempo estimado es de 3 a 5 días hábiles mediante Correos de Costa Rica. \n¿Cómo puedo devolver un producto? Si no está satisfecho con su compra, tiene 30 días naturales para solicitar una devolución. El producto debe estar en su empaque original y sin uso. Contacte a soporte@tienda.com para iniciar el proceso.",
  "metadata": {
    "client_id": "tienda-online-cr",
    "category": "faq_soporte",
    "url": "https://tienda.com/ayuda/envios",
    "source_timestamp": "2023-09-01T08:00:00Z",
    "tags": ["envios", "devoluciones", "garantia"]
  },
  "hash": "q1w2e3r4t5y6u7i8o9p0a1s2d3f4g5h6"
}
```

## 4. Lista de Precios de Servicios
```json
{
  "content_id": "serv-price-list-23",
  "source": "internal_erp",
  "title": "Tarifas de Servicios Profesionales 2024",
  "body_content": "Lista de precios actualizada para consultoría legal y notarial.\n1. Autenticación de firmas: ₡15,000 + IVA.\n2. Traspaso de vehículos: 2% del valor fiscal + timbres legales.\n3. Constitución de Sociedades Anónimas: $600 honorarios base.\n4. Asesoría por hora: $100.\nNota: Los precios están sujetos a cambios sin previo aviso. Descuentos disponibles para clientes corporativos.",
  "metadata": {
    "client_id": "bufete-legal",
    "category": "precios",
    "url": "internal://erp/precios/legal_2024",
    "source_timestamp": "2023-12-15T09:00:00Z",
    "moneda": "CRC/USD",
    "vigencia": "2024"
  },
  "hash": "m1n2b3v4c5x6z7a8s9d0f1g2h3j4k5l6"
}
```
