import logging
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.auth import hash_password

logger = logging.getLogger("salesia.init_db")

SCHEMA_STATEMENTS = [
    "CREATE SEQUENCE IF NOT EXISTS order_code_seq START 1001",
    """CREATE TABLE IF NOT EXISTS plans (
        id SERIAL PRIMARY KEY,
        code VARCHAR(50) UNIQUE NOT NULL,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        region_code VARCHAR(50) NOT NULL DEFAULT 'us-east-1',
        monthly_price NUMERIC(10,2) NOT NULL,
        setup_price NUMERIC(10,2) NOT NULL,
        active BOOLEAN NOT NULL DEFAULT true
    )""",
    """CREATE TABLE IF NOT EXISTS plan_components (
        id SERIAL PRIMARY KEY,
        plan_id INTEGER REFERENCES plans(id) ON DELETE CASCADE,
        service_code VARCHAR(50) NOT NULL,
        params JSONB NOT NULL DEFAULT '{}'
    )""",
    """CREATE TABLE IF NOT EXISTS extras (
        id SERIAL PRIMARY KEY,
        code VARCHAR(50) UNIQUE NOT NULL,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        monthly_price NUMERIC(10,2) NOT NULL,
        setup_price NUMERIC(10,2) NOT NULL,
        active BOOLEAN NOT NULL DEFAULT true
    )""",
    """CREATE TABLE IF NOT EXISTS customers (
        id SERIAL PRIMARY KEY,
        company_name VARCHAR(200) NOT NULL,
        ruc VARCHAR(20) UNIQUE NOT NULL,
        contact_name VARCHAR(200) NOT NULL,
        email VARCHAR(150) NOT NULL,
        phone VARCHAR(50),
        region VARCHAR(100),
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS staff_users (
        id SERIAL PRIMARY KEY,
        full_name VARCHAR(150) NOT NULL,
        email VARCHAR(150) UNIQUE NOT NULL,
        role VARCHAR(50) NOT NULL,
        password_hash TEXT NOT NULL,
        active BOOLEAN NOT NULL DEFAULT true,
        last_login_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )""",
    "ALTER TABLE staff_users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMPTZ",
    """CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY,
        code VARCHAR(50) UNIQUE NOT NULL DEFAULT ('PED-' || lpad(CAST(nextval('order_code_seq') AS text), 4, '0')),
        customer_id INTEGER REFERENCES customers(id),
        plan_id INTEGER REFERENCES plans(id),
        region_code VARCHAR(50) NOT NULL,
        monthly_total NUMERIC(10,2) NOT NULL,
        setup_total NUMERIC(10,2) NOT NULL,
        infra_usd NUMERIC(10,4) NOT NULL DEFAULT 0,
        infra_estimate NUMERIC(10,2) NOT NULL DEFAULT 0,
        fx_rate NUMERIC(10,4) NOT NULL DEFAULT 3.75,
        status VARCHAR(50) NOT NULL DEFAULT 'pendiente',
        risk VARCHAR(50) NOT NULL DEFAULT 'bajo',
        assigned_to INTEGER REFERENCES staff_users(id),
        reviewed_by INTEGER REFERENCES staff_users(id),
        reviewed_at TIMESTAMPTZ,
        reject_reason TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS order_items (
        id SERIAL PRIMARY KEY,
        order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
        extra_id INTEGER REFERENCES extras(id),
        extra_name VARCHAR(100) NOT NULL,
        monthly_price NUMERIC(10,2) NOT NULL,
        setup_price NUMERIC(10,2) NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 1
    )""",
    """CREATE TABLE IF NOT EXISTS order_components (
        id SERIAL PRIMARY KEY,
        order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
        service_code VARCHAR(50) NOT NULL,
        params JSONB NOT NULL DEFAULT '{}',
        usd_monthly NUMERIC(10,4) NOT NULL DEFAULT 0,
        breakdown JSONB NOT NULL DEFAULT '[]'
    )""",
    """CREATE TABLE IF NOT EXISTS order_reviews (
        id SERIAL PRIMARY KEY,
        order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
        summary TEXT NOT NULL,
        flags JSONB NOT NULL DEFAULT '{}',
        risk VARCHAR(50) NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS order_events (
        id SERIAL PRIMARY KEY,
        order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
        event_type VARCHAR(50) NOT NULL,
        description TEXT NOT NULL,
        actor_id INTEGER REFERENCES staff_users(id),
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS audit_log (
        id SERIAL PRIMARY KEY,
        actor_id INTEGER REFERENCES staff_users(id),
        action VARCHAR(100) NOT NULL,
        entity VARCHAR(50),
        entity_id VARCHAR(50),
        detail JSONB NOT NULL DEFAULT '{}',
        ip VARCHAR(50),
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS app_settings (
        key VARCHAR(100) PRIMARY KEY,
        value TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS aws_regions (
        code VARCHAR(50) PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        city VARCHAR(100),
        country VARCHAR(100),
        lat NUMERIC(10,6),
        lng NUMERIC(10,6),
        price_factor NUMERIC(6,4) NOT NULL DEFAULT 1.0
    )""",
    """CREATE TABLE IF NOT EXISTS aws_services (
        code VARCHAR(50) PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        category VARCHAR(100),
        description TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS aws_fx_rates (
        currency VARCHAR(10) PRIMARY KEY,
        per_usd NUMERIC(10,4) NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS aws_rates (
        id SERIAL PRIMARY KEY,
        service_code VARCHAR(50) NOT NULL,
        rate_key VARCHAR(100) NOT NULL,
        label VARCHAR(100),
        unit VARCHAR(50),
        value NUMERIC(14,6) NOT NULL,
        attributes JSONB NOT NULL DEFAULT '{}',
        UNIQUE(service_code, rate_key)
    )""",
]

SEED_STATEMENTS = [
    """INSERT INTO app_settings (key, value) VALUES
        ('catalog_mode', 'simulation'),
        ('catalog_reference_date', '2026-10-28'),
        ('catalog_notice', 'Simulación académica con tarifas de referencia aproximadas. No es una cotización de AWS.'),
        ('igv', '0.18'),
        ('review_mode', 'heuristic'),
        ('review_provider', 'gemini'),
        ('review_model', 'gemini-flash-lite-latest')
    ON CONFLICT (key) DO NOTHING""",

    """INSERT INTO aws_fx_rates (currency, per_usd) VALUES
        ('PEN', 3.75),
        ('USD', 1.00)
    ON CONFLICT (currency) DO NOTHING""",

    """INSERT INTO aws_regions (code, name, city, country, lat, lng, price_factor) VALUES
        ('us-east-1', 'US East (N. Virginia)', 'North Virginia', 'United States', 38.130000, -78.450000, 1.0000),
        ('us-west-2', 'US West (Oregon)', 'Oregon', 'United States', 45.839900, -119.700600, 1.0000),
        ('sa-east-1', 'South America (São Paulo)', 'São Paulo', 'Brazil', -23.550500, -46.633300, 1.5500),
        ('eu-west-1', 'Europe (Ireland)', 'Dublin', 'Ireland', 53.333100, -6.248900, 1.1200)
    ON CONFLICT (code) DO NOTHING""",

    """INSERT INTO aws_services (code, name, category, description) VALUES
        ('ec2', 'Amazon EC2', 'Cómputo', 'Servidores virtuales seguros y escalables en la nube'),
        ('rds', 'Amazon RDS', 'Base de datos', 'Base de datos relacional administrada para PostgreSQL y MySQL'),
        ('s3', 'Amazon S3', 'Almacenamiento', 'Almacenamiento de objetos con alta durabilidad y disponibilidad'),
        ('lambda', 'AWS Lambda', 'Serverless', 'Ejecución de código en respuesta a eventos sin aprovisionar servidores'),
        ('dynamodb', 'Amazon DynamoDB', 'Base de datos', 'Base de datos NoSQL rápida y flexible para latencia de milisegundos'),
        ('sns', 'Amazon SNS', 'Mensajería', 'Servicio de mensajería para notificaciones de publicación/suscripción'),
        ('cloudfront', 'Amazon CloudFront', 'Red de distribución', 'Red de entrega de contenido (CDN) segura y de baja latencia'),
        ('route53', 'Amazon Route 53', 'Redes y DNS', 'Servicio web DNS escalable y de alta disponibilidad')
    ON CONFLICT (code) DO NOTHING""",

    """INSERT INTO aws_rates (service_code, rate_key, label, unit, value, attributes) VALUES
        ('ec2', 'type:t3.micro', 't3.micro (2 vCPU, 1 GiB)', 'USD/hora', 0.0104, '{}'),
        ('ec2', 'type:t3.small', 't3.small (2 vCPU, 2 GiB)', 'USD/hora', 0.0208, '{}'),
        ('ec2', 'type:t3.medium', 't3.medium (2 vCPU, 4 GiB)', 'USD/hora', 0.0416, '{}'),
        ('ec2', 'os:linux', 'Linux', 'factor', 1.0, '{}'),
        ('ec2', 'config:monthly_hours', 'Horas al mes', 'horas', 730.0, '{}'),
        ('rds', 'type:db.t3.micro', 'db.t3.micro (2 vCPU, 1 GiB)', 'USD/hora', 0.017, '{}'),
        ('rds', 'type:db.t3.small', 'db.t3.small (2 vCPU, 2 GiB)', 'USD/hora', 0.034, '{}'),
        ('rds', 'storage:gp3_gb_month', 'Almacenamiento gp3', 'USD/GB-mes', 0.115, '{}'),
        ('rds', 'config:monthly_hours', 'Horas al mes', 'horas', 730.0, '{}'),
        ('rds', 'config:multi_az_factor', 'Multi-AZ', 'factor', 2.0, '{}'),
        ('s3', 'class:standard', 'S3 Standard', 'USD/GB-mes', 0.023, '{}'),
        ('lambda', 'request_per_million', 'Invocaciones', 'USD/millón', 0.20, '{}'),
        ('lambda', 'gb_second', 'Cómputo GB-segundo', 'USD/GB-s', 0.0000166667, '{}'),
        ('dynamodb', 'storage_gb_month', 'Almacenamiento DynamoDB', 'USD/GB-mes', 0.25, '{}'),
        ('dynamodb', 'rcu_hour', 'RCU por hora', 'USD/RCU-h', 0.000013, '{}'),
        ('dynamodb', 'wcu_hour', 'WCU por hora', 'USD/WCU-h', 0.000065, '{}'),
        ('sns', 'request_per_million', 'Publicaciones SNS', 'USD/millón', 0.50, '{}'),
        ('cloudfront', 'data_out_gb', 'Salida de datos CloudFront', 'USD/GB', 0.085, '{}'),
        ('route53', 'hosted_zone_month', 'Zona hospedada Route 53', 'USD/mes', 0.50, '{}'),
        ('route53', 'query_per_million', 'Consultas Route 53', 'USD/millón', 0.40, '{}')
    ON CONFLICT (service_code, rate_key) DO NOTHING""",

    """INSERT INTO plans (code, name, description, region_code, monthly_price, setup_price, active) VALUES
        ('arranque', 'Arranque', 'Página informativa con dominio, correo corporativo y respaldo.', 'us-east-1', 89.00, 199.00, true),
        ('negocio', 'Negocio', 'Tienda o catálogo con pedidos, pasarela de pago y panel de administración.', 'us-east-1', 189.00, 399.00, true),
        ('crece', 'Crece', 'Web corporativa y app móvil nativa con soporte prioritario 24/7.', 'us-east-1', 349.00, 699.00, true)
    ON CONFLICT (code) DO NOTHING""",

    """INSERT INTO extras (code, name, description, monthly_price, setup_price, active) VALUES
        ('dominio', 'Dominio personalizado (.pe o .com)', 'Registro y renovación anual incluida de dominio propio.', 15.00, 0.00, true),
        ('correo', 'Buzones corporativos adicionales', '3 cuentas de correo profesional con 10 GB de capacidad cada una.', 25.00, 0.00, true),
        ('soporte', 'Soporte prioritario 24/7', 'Atención directa vía WhatsApp y tiempo de respuesta menor a 1 hora.', 99.00, 0.00, true),
        ('app', 'App móvil Android e iOS', 'Aplicación móvil publicada en Google Play y App Store.', 150.00, 299.00, true),
        ('backup', 'Respaldo diario automatizado', 'Copias de seguridad diarias en S3 con retención de 30 días.', 35.00, 0.00, true)
    ON CONFLICT (code) DO NOTHING""",

    """INSERT INTO plan_components (plan_id, service_code, params)
    SELECT p.id, 's3', CAST('{"storageGb": 10, "storageClass": "standard"}' AS jsonb)
    FROM plans p WHERE p.code = 'arranque'
    AND NOT EXISTS (SELECT 1 FROM plan_components pc WHERE pc.plan_id = p.id AND pc.service_code = 's3')""",

    """INSERT INTO plan_components (plan_id, service_code, params)
    SELECT p.id, 'route53', CAST('{"zones": 1, "queriesMillions": 0.5}' AS jsonb)
    FROM plans p WHERE p.code = 'arranque'
    AND NOT EXISTS (SELECT 1 FROM plan_components pc WHERE pc.plan_id = p.id AND pc.service_code = 'route53')""",

    """INSERT INTO plan_components (plan_id, service_code, params)
    SELECT p.id, 'ec2', CAST('{"instanceType": "t3.micro", "os": "linux", "hoursPerMonth": 730, "instanceCount": 1}' AS jsonb)
    FROM plans p WHERE p.code = 'negocio'
    AND NOT EXISTS (SELECT 1 FROM plan_components pc WHERE pc.plan_id = p.id AND pc.service_code = 'ec2')""",

    """INSERT INTO plan_components (plan_id, service_code, params)
    SELECT p.id, 'rds', CAST('{"instanceType": "db.t3.micro", "engine": "postgresql", "multiAz": false, "storageGb": 20}' AS jsonb)
    FROM plans p WHERE p.code = 'negocio'
    AND NOT EXISTS (SELECT 1 FROM plan_components pc WHERE pc.plan_id = p.id AND pc.service_code = 'rds')""",

    """INSERT INTO plan_components (plan_id, service_code, params)
    SELECT p.id, 's3', CAST('{"storageGb": 50, "storageClass": "standard"}' AS jsonb)
    FROM plans p WHERE p.code = 'negocio'
    AND NOT EXISTS (SELECT 1 FROM plan_components pc WHERE pc.plan_id = p.id AND pc.service_code = 's3')""",

    """INSERT INTO plan_components (plan_id, service_code, params)
    SELECT p.id, 'route53', CAST('{"zones": 1, "queriesMillions": 1}' AS jsonb)
    FROM plans p WHERE p.code = 'negocio'
    AND NOT EXISTS (SELECT 1 FROM plan_components pc WHERE pc.plan_id = p.id AND pc.service_code = 'route53')""",

    """INSERT INTO plan_components (plan_id, service_code, params)
    SELECT p.id, 'ec2', CAST('{"instanceType": "t3.small", "os": "linux", "hoursPerMonth": 730, "instanceCount": 2}' AS jsonb)
    FROM plans p WHERE p.code = 'crece'
    AND NOT EXISTS (SELECT 1 FROM plan_components pc WHERE pc.plan_id = p.id AND pc.service_code = 'ec2')""",

    """INSERT INTO plan_components (plan_id, service_code, params)
    SELECT p.id, 'rds', CAST('{"instanceType": "db.t3.small", "engine": "postgresql", "multiAz": true, "storageGb": 50}' AS jsonb)
    FROM plans p WHERE p.code = 'crece'
    AND NOT EXISTS (SELECT 1 FROM plan_components pc WHERE pc.plan_id = p.id AND pc.service_code = 'rds')""",

    """INSERT INTO plan_components (plan_id, service_code, params)
    SELECT p.id, 's3', CAST('{"storageGb": 100, "storageClass": "standard"}' AS jsonb)
    FROM plans p WHERE p.code = 'crece'
    AND NOT EXISTS (SELECT 1 FROM plan_components pc WHERE pc.plan_id = p.id AND pc.service_code = 's3')""",

    """INSERT INTO plan_components (plan_id, service_code, params)
    SELECT p.id, 'cloudfront', CAST('{"dataOutGb": 200}' AS jsonb)
    FROM plans p WHERE p.code = 'crece'
    AND NOT EXISTS (SELECT 1 FROM plan_components pc WHERE pc.plan_id = p.id AND pc.service_code = 'cloudfront')""",

    """INSERT INTO plan_components (plan_id, service_code, params)
    SELECT p.id, 'route53', CAST('{"zones": 1, "queriesMillions": 2}' AS jsonb)
    FROM plans p WHERE p.code = 'crece'
    AND NOT EXISTS (SELECT 1 FROM plan_components pc WHERE pc.plan_id = p.id AND pc.service_code = 'route53')""",

    """INSERT INTO customers (company_name, ruc, contact_name, email, phone, region) VALUES
        ('Andes Café S.A.C.', '20601234561', 'Valeria Rojas', 'valeria@andescafe.example', '+51 987 654 321', 'Lima'),
        ('Textiles Inti S.A.C.', '20602345672', 'José Huamán', 'jose@inti.example', '+51 984 567 890', 'Arequipa'),
        ('Bodega Don Lucho', '20603456783', 'Luis Quispe', 'luis@donlucho.example', '+51 951 234 567', 'Lima')
    ON CONFLICT (ruc) DO NOTHING""",
]


def init_db(engine) -> None:
    # Only run full schema init on PostgreSQL
    if "postgresql" not in str(engine.url):
        return

    logger.info("Iniciando DDL de tablas...")
    with engine.begin() as conn:
        for stmt in SCHEMA_STATEMENTS:
            cleaned = stmt.strip()
            if cleaned:
                conn.execute(text(cleaned))

        for stmt in SEED_STATEMENTS:
            cleaned = stmt.strip()
            if cleaned:
                conn.execute(text(cleaned))

    # Add default admin user if no staff users exist
    with Session(engine) as session:
        count = session.execute(text("SELECT count(*) FROM staff_users")).scalar() or 0
        if count == 0:
            logger.info("Creando usuarios iniciales...")
            admin_hash = hash_password("Admin1234!")
            vendedor_hash = hash_password("Vendedor1234!")
            session.execute(
                text(
                    "INSERT INTO staff_users (full_name, email, role, password_hash, active) VALUES "
                    "('Administrador SalesIA', 'admin@salesia.com', 'administrador', :admin_hash, true), "
                    "('Lucía Torres', 'lucia@salesia.example', 'vendedor', :vendedor_hash, true)"
                ),
                {"admin_hash": admin_hash, "vendedor_hash": vendedor_hash},
            )
            session.commit()
    logger.info("Base de datos inicializada correctamente.")
