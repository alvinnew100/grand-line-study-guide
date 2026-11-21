-- A small food-centre ordering database for the Databases and SQL lesson (SQLite dialect).
CREATE TABLE stalls (
  stall_id INTEGER PRIMARY KEY,
  name     TEXT NOT NULL,
  cuisine  TEXT NOT NULL
);

CREATE TABLE dishes (
  dish_id     INTEGER PRIMARY KEY,
  stall_id    INTEGER NOT NULL REFERENCES stalls(stall_id),
  name        TEXT NOT NULL,
  price_cents INTEGER NOT NULL
);

CREATE TABLE customers (
  customer_id INTEGER PRIMARY KEY,
  name        TEXT NOT NULL,
  joined      TEXT NOT NULL
);

CREATE TABLE orders (
  order_id    INTEGER PRIMARY KEY,
  customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
  ordered_on  TEXT NOT NULL
);

CREATE TABLE order_items (
  order_id INTEGER NOT NULL REFERENCES orders(order_id),
  dish_id  INTEGER NOT NULL REFERENCES dishes(dish_id),
  quantity INTEGER NOT NULL,
  PRIMARY KEY (order_id, dish_id)
);

INSERT INTO stalls (stall_id, name, cuisine) VALUES
  (1, 'Ah Seng Chicken Rice', 'Chinese'),
  (2, 'Warung Sari', 'Malay'),
  (3, 'Madras Corner', 'Indian'),
  (4, 'Green Bowl', 'Salad');

INSERT INTO dishes (dish_id, stall_id, name, price_cents) VALUES
  (1, 1, 'Chicken rice', 450),
  (2, 1, 'Roasted pork rice', 500),
  (3, 2, 'Nasi lemak', 400),
  (4, 2, 'Mee rebus', 380),
  (5, 2, 'Satay set', 600),
  (6, 3, 'Roti prata', 250),
  (7, 3, 'Thosai', 300),
  (8, 3, 'Fish curry', 650);

INSERT INTO customers (customer_id, name, joined) VALUES
  (1, 'Aisha', '2025-01-10'),
  (2, 'Bao', '2025-02-03'),
  (3, 'Chandra', '2025-02-20'),
  (4, 'Devi', '2025-03-15'),
  (5, 'Ethan', '2025-04-01');

INSERT INTO orders (order_id, customer_id, ordered_on) VALUES
  (101, 1, '2025-05-01'),
  (102, 2, '2025-05-01'),
  (103, 1, '2025-05-02'),
  (104, 3, '2025-05-02'),
  (105, 4, '2025-05-03'),
  (106, 2, '2025-05-04'),
  (107, 1, '2025-05-04');

INSERT INTO order_items (order_id, dish_id, quantity) VALUES
  (101, 1, 2),
  (101, 6, 1),
  (102, 3, 1),
  (102, 5, 1),
  (103, 7, 2),
  (104, 2, 1),
  (104, 4, 1),
  (105, 3, 3),
  (106, 1, 1),
  (107, 5, 2),
  (107, 6, 2);
