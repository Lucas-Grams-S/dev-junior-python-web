-- MiniShop: banco de exemplo (schema + dados). Gerado de forma determinística.
-- Uso:  psql -U postgres -d loja -f loja.sql        (recria as tabelas do zero)
SET client_min_messages = warning;
DROP TABLE IF EXISTS payments, order_items, orders, cart_items, carts, products, categories, users CASCADE;

CREATE TABLE categories (
    id    integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name  text NOT NULL UNIQUE,
    slug  text NOT NULL UNIQUE
);

CREATE TABLE products (
    id           integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    category_id  integer       NOT NULL REFERENCES categories (id),
    sku          text          NOT NULL UNIQUE,
    slug         text          NOT NULL UNIQUE,
    name         text          NOT NULL,
    description  text          NOT NULL DEFAULT '',
    price        numeric(10,2) NOT NULL CHECK (price >= 0),
    stock        integer       NOT NULL DEFAULT 0 CHECK (stock >= 0),
    is_active    boolean       NOT NULL DEFAULT true,
    created_at   timestamptz   NOT NULL DEFAULT now()
);

CREATE TABLE users (
    id          integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email       text        NOT NULL UNIQUE,
    name        text        NOT NULL,
    is_staff    boolean     NOT NULL DEFAULT false,
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE carts (
    id          integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id     integer     NOT NULL UNIQUE REFERENCES users (id) ON DELETE CASCADE,
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE cart_items (
    cart_id     integer NOT NULL REFERENCES carts (id) ON DELETE CASCADE,
    product_id  integer NOT NULL REFERENCES products (id),
    quantity    integer NOT NULL CHECK (quantity > 0),
    PRIMARY KEY (cart_id, product_id)
);

CREATE TABLE orders (
    id          integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id     integer       NOT NULL REFERENCES users (id),
    status      text          NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'cancelled')),
    total       numeric(12,2) NOT NULL CHECK (total >= 0),
    created_at  timestamptz   NOT NULL DEFAULT now()
);

CREATE TABLE order_items (
    id          integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id    integer       NOT NULL REFERENCES orders (id) ON DELETE CASCADE,
    product_id  integer       NOT NULL REFERENCES products (id),
    quantity    integer       NOT NULL CHECK (quantity > 0),
    unit_price  numeric(10,2) NOT NULL CHECK (unit_price >= 0),
    UNIQUE (order_id, product_id)
);

CREATE TABLE payments (
    id            integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id      integer     NOT NULL UNIQUE REFERENCES orders (id),
    provider_ref  text        NOT NULL UNIQUE,
    status        text        NOT NULL CHECK (status IN ('approved', 'refused', 'refunded')),
    paid_at       timestamptz
);

INSERT INTO categories (name, slug) VALUES
    ('Periféricos', 'perifericos'),
    ('Áudio', 'audio'),
    ('Monitores', 'monitores'),
    ('Cabos e adaptadores', 'cabos-e-adaptadores'),
    ('Armazenamento', 'armazenamento');

INSERT INTO products (category_id, sku, slug, name, description, price, stock, is_active, created_at) VALUES
    (1, 'PF-01', 'mouse-sem-fio', 'Mouse sem fio', '', 89.90, 4, true, '2026-01-05 10:00:00+00:00'),
    (1, 'PF-02', 'mouse-gamer-rgb', 'Mouse gamer RGB', '', 159.90, 11, true, '2026-01-06 10:00:00+00:00'),
    (1, 'PF-03', 'teclado-mecanico', 'Teclado mecânico', '', 329.00, 18, true, '2026-01-07 10:00:00+00:00'),
    (1, 'PF-04', 'teclado-compacto', 'Teclado compacto', '', 149.90, 25, true, '2026-01-08 10:00:00+00:00'),
    (1, 'PF-05', 'webcam-full-hd', 'Webcam Full HD', '', 219.90, 0, true, '2026-01-09 10:00:00+00:00'),
    (1, 'PF-06', 'mousepad-grande', 'Mousepad grande', '', 59.90, 39, true, '2026-01-10 10:00:00+00:00'),
    (1, 'PF-07', 'hub-usb-4-portas', 'Hub USB 4 portas', '', 79.90, 6, true, '2026-01-11 10:00:00+00:00'),
    (1, 'PF-08', 'suporte-para-notebook', 'Suporte para notebook', '', 119.90, 13, true, '2026-01-12 10:00:00+00:00'),
    (1, 'PF-09', 'leitor-de-cartao-sd', 'Leitor de cartão SD', '', 39.90, 20, true, '2026-01-13 10:00:00+00:00'),
    (1, 'PF-10', 'apresentador-laser', 'Apresentador laser', '', 129.90, 27, false, '2026-01-14 10:00:00+00:00'),
    (2, 'AU-01', 'fone-bluetooth', 'Fone Bluetooth', '', 249.90, 34, true, '2026-01-15 10:00:00+00:00'),
    (2, 'AU-02', 'fone-com-fio', 'Fone com fio', '', 69.90, 1, true, '2026-01-16 10:00:00+00:00'),
    (2, 'AU-03', 'headset-gamer', 'Headset gamer', '', 299.90, 8, true, '2026-01-17 10:00:00+00:00'),
    (2, 'AU-04', 'caixa-de-som-portatil', 'Caixa de som portátil', '', 179.90, 15, true, '2026-01-18 10:00:00+00:00'),
    (2, 'AU-05', 'caixa-de-som-2-1', 'Caixa de som 2.1', '', 199.90, 22, true, '2026-01-19 10:00:00+00:00'),
    (2, 'AU-06', 'microfone-usb', 'Microfone USB', '', 349.90, 29, true, '2026-01-20 10:00:00+00:00'),
    (2, 'AU-07', 'microfone-de-lapela', 'Microfone de lapela', '', 99.90, 36, true, '2026-01-21 10:00:00+00:00'),
    (2, 'AU-08', 'adaptador-de-audio-usb', 'Adaptador de áudio USB', '', 29.90, 0, true, '2026-01-22 10:00:00+00:00'),
    (2, 'AU-09', 'soundbar', 'Soundbar', '', 449.90, 10, true, '2026-01-23 10:00:00+00:00'),
    (2, 'AU-10', 'fone-intra-auricular', 'Fone intra-auricular', '', 49.90, 17, true, '2026-01-24 10:00:00+00:00'),
    (3, 'MN-01', 'monitor-21-polegadas-full-hd', 'Monitor 21 polegadas Full HD', '', 699.00, 24, true, '2026-01-25 10:00:00+00:00'),
    (3, 'MN-02', 'monitor-24-polegadas-full-hd', 'Monitor 24 polegadas Full HD', '', 849.00, 31, true, '2026-01-26 10:00:00+00:00'),
    (3, 'MN-03', 'monitor-27-polegadas-qhd', 'Monitor 27 polegadas QHD', '', 1399.00, 38, true, '2026-01-27 10:00:00+00:00'),
    (3, 'MN-04', 'monitor-27-polegadas-4k', 'Monitor 27 polegadas 4K', '', 2199.00, 5, true, '2026-01-28 10:00:00+00:00'),
    (3, 'MN-05', 'monitor-curvo-32-polegadas', 'Monitor curvo 32 polegadas', '', 1899.00, 12, true, '2026-01-29 10:00:00+00:00'),
    (3, 'MN-06', 'monitor-portatil-15-polegadas', 'Monitor portátil 15 polegadas', '', 999.00, 19, true, '2026-01-30 10:00:00+00:00'),
    (3, 'MN-07', 'suporte-articulado-para-monitor', 'Suporte articulado para monitor', '', 189.90, 26, true, '2026-01-31 10:00:00+00:00'),
    (3, 'MN-08', 'pelicula-antirreflexo-24-polegadas', 'Película antirreflexo 24 polegadas', '', 79.90, 33, true, '2026-02-01 10:00:00+00:00'),
    (3, 'MN-09', 'barra-de-luz-para-monitor', 'Barra de luz para monitor', '', 159.90, 40, true, '2026-02-02 10:00:00+00:00'),
    (3, 'MN-10', 'monitor-ultrawide-34-polegadas', 'Monitor ultrawide 34 polegadas', '', 2899.00, 7, false, '2026-02-03 10:00:00+00:00'),
    (4, 'CB-01', 'cabo-hdmi-2m', 'Cabo HDMI 2m', '', 29.90, 14, true, '2026-02-04 10:00:00+00:00'),
    (4, 'CB-02', 'cabo-hdmi-5m', 'Cabo HDMI 5m', '', 49.90, 21, true, '2026-02-05 10:00:00+00:00'),
    (4, 'CB-03', 'cabo-displayport-1-8m', 'Cabo DisplayPort 1,8m', '', 44.90, 28, true, '2026-02-06 10:00:00+00:00'),
    (4, 'CB-04', 'cabo-usb-c-1m', 'Cabo USB-C 1m', '', 24.90, 0, true, '2026-02-07 10:00:00+00:00'),
    (4, 'CB-05', 'cabo-usb-c-2m', 'Cabo USB-C 2m', '', 34.90, 2, true, '2026-02-08 10:00:00+00:00'),
    (4, 'CB-06', 'cabo-de-rede-cat6-5m', 'Cabo de rede Cat6 5m', '', 27.90, 9, true, '2026-02-09 10:00:00+00:00'),
    (4, 'CB-07', 'adaptador-hdmi-para-vga', 'Adaptador HDMI para VGA', '', 39.90, 16, true, '2026-02-10 10:00:00+00:00'),
    (4, 'CB-08', 'adaptador-usb-c-para-hdmi', 'Adaptador USB-C para HDMI', '', 89.90, 23, true, '2026-02-11 10:00:00+00:00'),
    (4, 'CB-09', 'extensao-usb-3-0', 'Extensão USB 3.0', '', 34.90, 30, true, '2026-02-12 10:00:00+00:00'),
    (4, 'CB-10', 'regua-de-tomadas-6-saidas', 'Régua de tomadas 6 saídas', '', 69.90, 37, true, '2026-02-13 10:00:00+00:00'),
    (5, 'AR-01', 'ssd-240-gb', 'SSD 240 GB', '', 169.90, 4, true, '2026-02-14 10:00:00+00:00'),
    (5, 'AR-02', 'ssd-480-gb', 'SSD 480 GB', '', 249.90, 11, true, '2026-02-15 10:00:00+00:00'),
    (5, 'AR-03', 'ssd-1-tb', 'SSD 1 TB', '', 449.90, 18, true, '2026-02-16 10:00:00+00:00'),
    (5, 'AR-04', 'ssd-nvme-1-tb', 'SSD NVMe 1 TB', '', 549.90, 25, true, '2026-02-17 10:00:00+00:00'),
    (5, 'AR-05', 'hd-externo-1-tb', 'HD externo 1 TB', '', 379.90, 32, false, '2026-02-18 10:00:00+00:00'),
    (5, 'AR-06', 'hd-externo-2-tb', 'HD externo 2 TB', '', 549.90, 39, true, '2026-02-19 10:00:00+00:00'),
    (5, 'AR-07', 'pen-drive-64-gb', 'Pen drive 64 GB', '', 39.90, 6, true, '2026-02-20 10:00:00+00:00'),
    (5, 'AR-08', 'pen-drive-128-gb', 'Pen drive 128 GB', '', 59.90, 13, true, '2026-02-21 10:00:00+00:00'),
    (5, 'AR-09', 'cartao-microsd-128-gb', 'Cartão microSD 128 GB', '', 69.90, 20, true, '2026-02-22 10:00:00+00:00'),
    (5, 'AR-10', 'case-para-ssd-nvme', 'Case para SSD NVMe', '', 99.90, 27, true, '2026-02-23 10:00:00+00:00');

INSERT INTO users (email, name, is_staff, created_at) VALUES
    ('ana@exemplo.test', 'Ana Souza', false, '2026-01-05 10:00:00+00:00'),
    ('bruno@exemplo.test', 'Bruno Lima', false, '2026-01-06 10:00:00+00:00'),
    ('carla@exemplo.test', 'Carla Mendes', false, '2026-01-07 10:00:00+00:00'),
    ('diego@exemplo.test', 'Diego Alves', false, '2026-01-08 10:00:00+00:00'),
    ('elisa@exemplo.test', 'Elisa Prado', false, '2026-01-09 10:00:00+00:00'),
    ('admin@minishop.test', 'Administrador', true, '2026-01-10 10:00:00+00:00');

INSERT INTO orders (user_id, status, total, created_at) VALUES
    (1, 'pending', 33.16, '2026-02-23 17:37:00+00:00'),
    (1, 'paid', 99.48, '2026-03-10 22:05:00+00:00'),
    (2, 'paid', 483.35, '2026-03-15 22:19:00+00:00'),
    (2, 'cancelled', 66.32, '2026-03-31 18:36:00+00:00'),
    (2, 'paid', 5639.85, '2026-04-14 14:52:00+00:00'),
    (1, 'paid', 154.50, '2026-05-05 14:30:00+00:00'),
    (4, 'paid', 7395.60, '2026-05-15 17:58:00+00:00'),
    (1, 'paid', 379.50, '2026-06-01 18:13:00+00:00'),
    (2, 'pending', 404.50, '2026-06-13 15:24:00+00:00'),
    (4, 'paid', 10913.80, '2026-06-29 18:53:00+00:00'),
    (4, 'cancelled', 899.80, '2026-07-12 14:35:00+00:00'),
    (3, 'paid', 1289.30, '2026-07-20 14:31:00+00:00'),
    (2, 'paid', 4957.60, '2026-08-07 14:11:00+00:00'),
    (1, 'paid', 399.20, '2026-08-19 17:23:00+00:00'),
    (4, 'cancelled', 2568.50, '2026-09-05 21:22:00+00:00'),
    (1, 'pending', 899.80, '2026-09-14 15:30:00+00:00'),
    (2, 'paid', 869.30, '2026-10-06 15:33:00+00:00'),
    (2, 'paid', 284.40, '2026-10-20 16:43:00+00:00');

INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
    (1, 39, 1, 33.16),
    (2, 39, 3, 33.16),
    (3, 3, 1, 312.55),
    (3, 38, 2, 85.40),
    (4, 39, 2, 33.16),
    (5, 25, 3, 1804.05),
    (5, 7, 3, 75.90),
    (6, 34, 3, 24.90),
    (6, 47, 2, 39.90),
    (7, 25, 3, 1899.00),
    (7, 21, 1, 699.00),
    (7, 17, 1, 99.90),
    (7, 13, 3, 299.90),
    (8, 50, 3, 99.90),
    (8, 31, 1, 29.90),
    (8, 20, 1, 49.90),
    (9, 11, 1, 249.90),
    (9, 34, 3, 24.90),
    (9, 28, 1, 79.90),
    (10, 23, 3, 1399.00),
    (10, 48, 2, 59.90),
    (10, 24, 3, 2199.00),
    (11, 19, 2, 449.90),
    (12, 44, 2, 549.90),
    (12, 39, 2, 34.90),
    (12, 47, 3, 39.90),
    (13, 24, 2, 2199.00),
    (13, 12, 1, 69.90),
    (13, 42, 1, 249.90),
    (13, 8, 2, 119.90),
    (14, 34, 2, 24.90),
    (14, 6, 3, 59.90),
    (14, 12, 2, 69.90),
    (14, 31, 1, 29.90),
    (15, 49, 3, 69.90),
    (15, 28, 2, 79.90),
    (15, 24, 1, 2199.00),
    (16, 16, 1, 349.90),
    (16, 46, 1, 549.90),
    (17, 20, 2, 49.90),
    (17, 1, 3, 89.90),
    (17, 11, 2, 249.90),
    (18, 48, 3, 59.90),
    (18, 35, 3, 34.90);

INSERT INTO payments (order_id, provider_ref, status, paid_at) VALUES
    (2, 'SIM-0002', 'approved', '2026-03-10 22:10:00+00:00'),
    (3, 'SIM-0003', 'approved', '2026-03-15 22:24:00+00:00'),
    (4, 'SIM-0004', 'refused', NULL),
    (5, 'SIM-0005', 'approved', '2026-04-14 14:57:00+00:00'),
    (6, 'SIM-0006', 'approved', '2026-05-05 14:35:00+00:00'),
    (7, 'SIM-0007', 'approved', '2026-05-15 18:03:00+00:00'),
    (8, 'SIM-0008', 'approved', '2026-06-01 18:18:00+00:00'),
    (10, 'SIM-0010', 'approved', '2026-06-29 18:58:00+00:00'),
    (12, 'SIM-0012', 'approved', '2026-07-20 14:36:00+00:00'),
    (13, 'SIM-0013', 'approved', '2026-08-07 14:16:00+00:00'),
    (14, 'SIM-0014', 'approved', '2026-08-19 17:28:00+00:00'),
    (17, 'SIM-0017', 'approved', '2026-10-06 15:38:00+00:00'),
    (18, 'SIM-0018', 'approved', '2026-10-20 16:48:00+00:00');

INSERT INTO carts (user_id) VALUES (2), (5);
INSERT INTO cart_items (cart_id, product_id, quantity) VALUES (1, 3, 1), (1, 7, 2), (2, 12, 1);
